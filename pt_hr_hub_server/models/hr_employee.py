# -*- coding: utf-8 -*-

import hmac
import math

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    require_face_attendance = fields.Boolean(string="Require Face Attendance", default=False)
    x_device_uuid = fields.Char(string="Device UUID")
    x_faceio_id = fields.Char(string="FaceIO Facial ID")
    x_geofence_enabled = fields.Boolean(string="Geo Fence Required", default=False)
    x_geofence_latitude = fields.Float(string="Geo Fence Latitude")
    x_geofence_longitude = fields.Float(string="Geo Fence Longitude")
    x_geofence_radius_m = fields.Float(string="Geo Fence Radius (m)", default=100.0)
    hub_client_config_id = fields.Many2one("hub.client.config", string="Hub Client")

    @api.constrains('x_faceio_id', 'x_device_uuid')
    def _check_subscription_limits(self):
        params = self.env['ir.config_parameter'].sudo()
        max_users_str = params.get_param('pt_hr_hub_server.subscription_max_users', '0')
        try:
            max_users = int(max_users_str)
        except ValueError:
            max_users = 0

        if max_users > 0:
            for record in self:
                if record.x_faceio_id or record.x_device_uuid:
                    count = self.env['hr.employee'].search_count([
                        '|', ('x_faceio_id', '!=', False), ('x_device_uuid', '!=', False)
                    ])
                    if count > max_users:
                        raise ValidationError(_("Mobile App Subscription user limit (%s) exceeded! Please contact support to upgrade your subscription.") % max_users)

    def _check_device_id(self, incoming_device_uuid):
        self.ensure_one()
        if self.x_device_uuid and self.x_device_uuid != incoming_device_uuid:
            raise ValidationError(_("Device mismatch for employee %s.") % self.display_name)
        return True

    def _verify_face_token(self, incoming_face_token):
        """Legacy token validation for backward compatibility."""
        self.ensure_one()
        if not self.x_faceio_id:
            raise ValidationError(_("FaceIO token is not configured for employee %s.") % self.display_name)
        if not incoming_face_token:
            raise ValidationError(_("Face token is required."))
        if not hmac.compare_digest(self.x_faceio_id, incoming_face_token):
            raise ValidationError(_("FaceIO token validation failed for employee %s.") % self.display_name)
        return True

    def _verify_faceio_id(self, incoming_faceio_id):
        self.ensure_one()
        if not self.x_faceio_id:
            raise ValidationError(_("FaceIO facial ID is not configured for employee %s.") % self.display_name)
        if not incoming_faceio_id:
            raise ValidationError(_("FaceIO facial ID is required."))
        if not hmac.compare_digest(self.x_faceio_id, incoming_faceio_id):
            raise ValidationError(_("FaceIO facial ID validation failed for employee %s.") % self.display_name)
        return True

    def _check_geofence(self, incoming_latitude, incoming_longitude):
        self.ensure_one()
        if not self.x_geofence_enabled:
            return True

        if self.x_geofence_radius_m <= 0:
            raise ValidationError(_("Geo fence radius must be greater than 0 for employee %s.") % self.display_name)

        if self.x_geofence_latitude is False or self.x_geofence_longitude is False:
            raise ValidationError(_("Geo fence latitude/longitude is not configured for employee %s.") % self.display_name)

        try:
            lat1 = math.radians(float(incoming_latitude))
            lon1 = math.radians(float(incoming_longitude))
            lat2 = math.radians(float(self.x_geofence_latitude))
            lon2 = math.radians(float(self.x_geofence_longitude))
        except Exception:
            raise ValidationError(_("Invalid location coordinates provided for employee %s.") % self.display_name)

        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        distance_m = 6371000.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        if distance_m > self.x_geofence_radius_m:
            raise ValidationError(
                _(
                    "Attendance location is outside geo fence for employee %s. "
                    "Distance: %.2f m, allowed radius: %.2f m."
                )
                % (self.display_name, distance_m, self.x_geofence_radius_m)
            )
        return True

    def action_open_faceio_enroll_page(self):
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "faceio_enrollment_action",
            "name": "FaceIO Enrollment",
            "target": "current",
            "context": {"employee_id": self.id},
        }
