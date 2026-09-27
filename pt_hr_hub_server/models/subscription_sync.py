# -*- coding: utf-8 -*-
import json
from urllib import request as url_request
from urllib import error as url_error

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    central_server_url = fields.Char(
        string="Central Server URL",
        config_parameter="pt_hr_hub_server.central_server_url"
    )
    subscription_code = fields.Char(
        string="Subscription Code",
        config_parameter="pt_hr_hub_server.subscription_code"
    )
    
    # Cached Subscription Details
    subscription_valid = fields.Boolean(
        string="Subscription Valid",
        config_parameter="pt_hr_hub_server.subscription_valid",
        readonly=True
    )
    subscription_max_users = fields.Integer(
        string="Max Users Allowed",
        config_parameter="pt_hr_hub_server.subscription_max_users",
        readonly=True
    )
    subscription_end_date = fields.Char(
        string="Subscription End Date",
        config_parameter="pt_hr_hub_server.subscription_end_date",
        readonly=True
    )

    def action_sync_subscription(self):
        self.ensure_one()
        url = self.central_server_url
        code = self.subscription_code
        
        if not url or not code:
            raise UserError(_("Please configure the Central Server URL and Subscription Code before syncing."))
            
        endpoint = f"{url.rstrip('/')}/api/subscription/validate"
        client_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        payload = json.dumps({
            "subscription_code": code,
            "server_url": client_url
        }).encode('utf-8')
        
        req = url_request.Request(endpoint, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
        
        try:
            with url_request.urlopen(req, timeout=15) as response:
                raw_body = response.read().decode('utf-8')
                result = json.loads(raw_body)
        except Exception as e:
            raise UserError(_("Failed to connect to the central server: %s") % str(e))
            
        if 'error' in result:
            self.env['ir.config_parameter'].sudo().set_param('pt_hr_hub_server.subscription_valid', "False")
            raise UserError(_("Subscription validation failed: %s") % result['error'])
            
        # Update settings
        valid = str(result.get('valid', False))
        self.env['ir.config_parameter'].sudo().set_param('pt_hr_hub_server.subscription_valid', valid)
        self.env['ir.config_parameter'].sudo().set_param('pt_hr_hub_server.subscription_max_users', str(result.get('max_users', 0)))
        
        if result.get('end_date'):
            self.env['ir.config_parameter'].sudo().set_param('pt_hr_hub_server.subscription_end_date', result['end_date'])
        else:
            self.env['ir.config_parameter'].sudo().set_param('pt_hr_hub_server.subscription_end_date', False)
            
        # Update FaceIO if provided
        faceio_app_id = result.get('faceio_app_public_id')
        faceio_secret = result.get('faceio_secret_key')
        faceio_endpoint = result.get('faceio_identity_endpoint')
        
        if faceio_app_id and faceio_secret:
            self.env['ir.config_parameter'].sudo().set_param('pt_hr_hub_server.faceio_enabled', 'True')
            self.env['ir.config_parameter'].sudo().set_param('pt_hr_hub_server.faceio_app_public_id', faceio_app_id)
            
            # Encrypt secret
            try:
                secret_encrypted = self.env['res.config.settings']._get_fernet().encrypt(faceio_secret.encode("utf-8")).decode("utf-8")
                self.env['ir.config_parameter'].sudo().set_param('pt_hr_hub_server.faceio_secret_key_encrypted', secret_encrypted)
            except Exception as e:
                pass # fail silently if fernet not available
                
            if faceio_endpoint:
                self.env['ir.config_parameter'].sudo().set_param('pt_hr_hub_server.faceio_identity_endpoint', faceio_endpoint)

        if result.get('valid'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Success"),
                    'message': _("Subscription synced successfully. Valid until %s. Max users: %s") % (result.get('end_date', 'Forever'), result.get('max_users', 'Unlimited')),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise UserError(_("Subscription synced, but it is currently INVALID or EXPIRED."))

