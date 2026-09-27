# -*- coding: utf-8 -*-

import base64
import hashlib
import json
from urllib import error as url_error
from urllib import parse as url_parse
from urllib import request as url_request

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

try:
    from cryptography.fernet import Fernet
except Exception:
    Fernet = None


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    faceio_enabled = fields.Boolean(
        string="Enable FaceIO Verification",
        config_parameter="pt_hr_hub_server.faceio_enabled",
    )
    faceio_app_public_id = fields.Char(
        string="FaceIO Public App ID",
        config_parameter="pt_hr_hub_server.faceio_app_public_id",
    )
    faceio_secret_key_encrypted = fields.Char(
        string="Encrypted FaceIO Secret",
        config_parameter="pt_hr_hub_server.faceio_secret_key_encrypted",
        copy=False,
    )
    faceio_secret_key = fields.Char(
        string="FaceIO Secret Key",
        compute="_compute_faceio_secret_key",
        inverse="_inverse_faceio_secret_key",
        password=True,
        store=False,
    )
    faceio_identity_endpoint = fields.Char(
        string="FaceIO Identity Endpoint",
        config_parameter="pt_hr_hub_server.faceio_identity_endpoint",
        default="https://api.faceio.net/v2/identities/{faceio_id}",
        help="Endpoint template used to validate identities. Use {faceio_id} placeholder.",
    )

    @api.model
    def _get_fernet(self):
        if Fernet is None:
            raise UserError(_("Package 'cryptography' is required to store encrypted API keys."))
        secret = self.env["ir.config_parameter"].sudo().get_param("database.secret") or self.env.cr.dbname
        key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
        return Fernet(key)

    def _compute_faceio_secret_key(self):
        for rec in self:
            rec.faceio_secret_key = rec._decrypt_secret(rec.faceio_secret_key_encrypted)

    def _inverse_faceio_secret_key(self):
        for rec in self:
            if rec.faceio_secret_key:
                rec.faceio_secret_key_encrypted = rec._get_fernet().encrypt(rec.faceio_secret_key.encode("utf-8")).decode("utf-8")
            else:
                rec.faceio_secret_key_encrypted = False

    def _decrypt_secret(self, encrypted_value):
        if not encrypted_value:
            return False
        try:
            return self._get_fernet().decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
        except Exception:
            return False


class HrFaceioEnrollment(models.TransientModel):
    """Wizard for testing and enrolling employees with FaceIO."""
    _name = "hr.faceio.enrollment"
    _description = "HR FaceIO Enrollment & Testing"

    employee_id = fields.Many2one("hr.employee", string="Employee", required=True, ondelete="cascade")
    faceio_id = fields.Char(string="FaceIO Facial ID", required=True)
    device_uuid = fields.Char(string="Device UUID")
    test_latitude = fields.Float(string="Test Latitude", default=0.0)
    test_longitude = fields.Float(string="Test Longitude", default=0.0)
    enrollment_status = fields.Text(string="Enrollment Status", readonly=True)

    def action_verify_faceio_id(self):
        """Test the FaceIO facial ID against FaceIO API."""
        self.ensure_one()
        config_params = self.env["ir.config_parameter"].sudo()
        faceio_enabled = config_params.get_param("pt_hr_hub_server.faceio_enabled")
        faceio_app_public_id = config_params.get_param("pt_hr_hub_server.faceio_app_public_id")
        faceio_secret_key_encrypted = config_params.get_param("pt_hr_hub_server.faceio_secret_key_encrypted")
        faceio_identity_endpoint = config_params.get_param("pt_hr_hub_server.faceio_identity_endpoint")

        if not faceio_enabled:
            raise ValidationError(_("FaceIO verification is not enabled in settings."))

        if not faceio_app_public_id or not faceio_secret_key_encrypted:
            raise ValidationError(_("FaceIO credentials are not configured in settings."))

        secret_key = self._decrypt_secret(faceio_secret_key_encrypted)
        if not secret_key:
            raise ValidationError(_("Unable to decrypt FaceIO Secret Key."))

        endpoint_template = faceio_identity_endpoint or "https://api.faceio.net/v2/identities/{faceio_id}"
        endpoint_templates = [endpoint_template]
        if "/v1/" in endpoint_template:
            endpoint_templates.append(endpoint_template.replace("/v1/", "/v2/", 1))

        unique_endpoint_templates = []
        for candidate in endpoint_templates:
            if candidate not in unique_endpoint_templates:
                unique_endpoint_templates.append(candidate)

        request_headers = {
            "Authorization": "Bearer %s" % secret_key,
            "X-FaceIO-App-Id": faceio_app_public_id,
            "Accept": "application/json",
        }
        raw_body = False
        last_http_error = False
        for endpoint_template_candidate in unique_endpoint_templates:
            endpoint = endpoint_template_candidate.format(faceio_id=url_parse.quote(self.faceio_id, safe=""))
            req = url_request.Request(endpoint, headers=request_headers, method="GET")
            try:
                with url_request.urlopen(req, timeout=15) as response:
                    raw_body = response.read().decode("utf-8")
                break
            except url_error.HTTPError as error:
                message = error.read().decode("utf-8", errors="ignore")
                last_http_error = (error.code, message or error.reason)
                if error.code == 404 and "No such API endpoint" in message and "/v1/" in endpoint_template_candidate:
                    continue
                self.enrollment_status = _("FaceIO verification failed (%s): %s") % (error.code, message or error.reason)
                return {"type": "ir.actions.act_window", "res_model": self._name, "res_id": self.id, "view_mode": "form"}

            except Exception as error:
                self.enrollment_status = _("Unable to reach FaceIO verification service: %s") % str(error)
                return {"type": "ir.actions.act_window", "res_model": self._name, "res_id": self.id, "view_mode": "form"}

        if not raw_body and last_http_error:
            self.enrollment_status = _("FaceIO verification failed (%s): %s") % last_http_error
            return {"type": "ir.actions.act_window", "res_model": self._name, "res_id": self.id, "view_mode": "form"}

        if not raw_body:
            self.enrollment_status = _("FaceIO verification returned an empty response.")
            return {"type": "ir.actions.act_window", "res_model": self._name, "res_id": self.id, "view_mode": "form"}

        try:
            payload = json.loads(raw_body)
        except Exception:
            self.enrollment_status = _("FaceIO verification returned an invalid JSON response.")
            return {"type": "ir.actions.act_window", "res_model": self._name, "res_id": self.id, "view_mode": "form"}

        candidates = {
            payload.get("facialId"),
            payload.get("faceio_id"),
            payload.get("faceioId"),
            payload.get("id"),
        }
        identity = payload.get("identity") if isinstance(payload.get("identity"), dict) else {}
        candidates.update({
            identity.get("facialId"),
            identity.get("faceio_id"),
            identity.get("id"),
        })

        if self.faceio_id not in candidates:
            self.enrollment_status = _("FaceIO identity response does not match the provided facial ID.")
            return {"type": "ir.actions.act_window", "res_model": self._name, "res_id": self.id, "view_mode": "form"}

        self.enrollment_status = _("✓ FaceIO identity verified successfully!")
        return {"type": "ir.actions.act_window", "res_model": self._name, "res_id": self.id, "view_mode": "form"}

    def action_save_enrollment(self):
        """Save the FaceIO facial ID to the employee and optionally register device."""
        self.ensure_one()
        self.action_verify_faceio_id()
        if "verified successfully" not in str(self.enrollment_status or ""):
            raise ValidationError(_("Cannot save enrollment: %s") % self.enrollment_status)

        self.employee_id.write({
            "x_faceio_id": self.faceio_id,
        })
        if self.device_uuid:
            self.employee_id.write({
                "x_device_uuid": self.device_uuid,
            })

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": _("Employee %s enrolled with FaceIO ID successfully.") % self.employee_id.display_name,
                "type": "success",
                "sticky": False,
            },
        }

    def action_test_attendance_creation(self):
        """Test creating an attendance record with the enrolled FaceIO ID."""
        self.ensure_one()
        if not self.employee_id.x_faceio_id:
            raise ValidationError(_("Employee has no FaceIO ID enrolled yet."))

        try:
            attendance = self.env["hr.attendance"].sudo().create_verified_attendance_from_hub({
                "employee_id": self.employee_id.id,
                "device_uuid": self.device_uuid or "test-device",
                "faceio_id": self.faceio_id,
                "lat": self.test_latitude,
                "long": self.test_longitude,
            })
            self.enrollment_status = _("✓ Attendance record created successfully (ID: %s)") % attendance.id
        except Exception as e:
            self.enrollment_status = _("Attendance creation test failed: %s") % str(e)

        return {"type": "ir.actions.act_window", "res_model": self._name, "res_id": self.id, "view_mode": "form"}

    @api.model
    def _get_fernet(self):
        if Fernet is None:
            raise UserError(_("Package 'cryptography' is required to store encrypted API keys."))
        secret = self.env["ir.config_parameter"].sudo().get_param("database.secret") or self.env.cr.dbname
        key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
        return Fernet(key)

    def _decrypt_secret(self, encrypted_value):
        if not encrypted_value:
            return False
        try:
            return self._get_fernet().decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
        except Exception:
            return False
