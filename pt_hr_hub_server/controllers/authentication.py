# -*- coding: utf-8 -*-
import json
import logging
from datetime import date

from odoo import fields
from odoo.http import request, Response
from odoo.addons.muk_rest.controllers.authentication import AuthenticationController

_logger = logging.getLogger(__name__)

class PTAuthenticationController(AuthenticationController):

    def oauth2_token(self, **kw):
        """
        Override the default muk_rest OAuth2 token generation to enforce
        mobile app subscription limits.
        """
        params = request.env['ir.config_parameter'].sudo()
        is_valid_str = params.get_param('pt_hr_hub_server.subscription_valid')
        end_date_str = params.get_param('pt_hr_hub_server.subscription_end_date')
        
        if is_valid_str == 'False':
            _logger.warning("Mobile App Login blocked: Subscription is invalid!")
            return Response(
                response=json.dumps({
                    "error": "access_denied", 
                    "error_description": "Mobile App Subscription Invalid. Please contact support."
                }),
                status=401,
                headers=[('Content-Type', 'application/json')]
            )
            
        if end_date_str:
            try:
                end_date = fields.Date.from_string(end_date_str)
                if end_date < date.today():
                    _logger.warning("Mobile App Login blocked: Client Subscription Expired!")
                    return Response(
                        response=json.dumps({
                            "error": "access_denied", 
                            "error_description": "Mobile App Subscription Expired. Please contact support."
                        }),
                        status=401,
                        headers=[('Content-Type', 'application/json')]
                    )
            except Exception as e:
                _logger.error("Failed to validate subscription date: %s", str(e))
                
        # If subscription is valid, proceed with standard token generation
        response = super(PTAuthenticationController, self).oauth2_token(**kw)
        
        # If login was successful (status 200), enrich the response with app settings
        if response.status_code == 200:
            try:
                data = json.loads(response.data)
                
                # Get authenticated user's employee
                user = request.env['res.users'].sudo().search([('login', '=', kw.get('username'))], limit=1)
                employee = user.employee_id or request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
                
                config = request.env['ir.config_parameter'].sudo()
                
                # App Settings
                data['app_settings'] = {
                    'faceio_enabled': config.get_param('pt_hr_hub_server.faceio_enabled') == 'True',
                    'faceio_public_id': config.get_param('pt_hr_hub_server.faceio_app_public_id'),
                }
                
                # User/Employee Details
                if employee:
                    data['employee'] = {
                        'id': employee.id,
                        'name': employee.name,
                        'require_face_attendance': employee.require_face_attendance,
                        'device_uuid': employee.x_device_uuid,
                        'faceio_id': employee.x_faceio_id,
                        'geofence': {
                            'enabled': employee.x_geofence_enabled,
                            'lat': employee.x_geofence_latitude,
                            'long': employee.x_geofence_longitude,
                            'radius': employee.x_geofence_radius_m,
                        }
                    }
                
                response.data = json.dumps(data)
            except Exception as e:
                _logger.error("Failed to enrich OAuth2 response: %s", str(e))
                
        return response
