# -*- coding: utf-8 -*-

import logging
import base64
import hashlib
import xmlrpc.client
from urllib import error as url_error
from urllib import parse as url_parse
from urllib import request as url_request
import json
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

try:
    from cryptography.fernet import Fernet
except Exception:
    Fernet = None

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    x_latitude = fields.Float(string="Latitude")
    x_longitude = fields.Float(string="Longitude")
    x_device_id_used = fields.Char(string="Device ID Used")
    x_hub_verified = fields.Boolean(default=False, readonly=True, copy=False)
    x_sync_state = fields.Selection(
        selection=[("no_target", "No Target"), ("pending", "Pending"), ("done", "Done"), ("failed", "Failed")],
        string="Hub Sync State",
        default="no_target",
        copy=False,
        readonly=True,
    )
    x_sync_error = fields.Text(string="Hub Sync Error", readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("hub_attendance_verified"):
            return records

        queue_model = self.env["hub.attendance.sync.queue"]
        for attendance in records:
            client_config = attendance.employee_id.hub_client_config_id or self.env["hub.client.config"].search([("active", "=", True)], limit=1)
            if not client_config:
                attendance.write({
                    "x_hub_verified": True,
                    "x_sync_state": "no_target",
                    "x_sync_error": _("No active hub.client.config found."),
                })
                continue

            queue_model.create({
                "attendance_id": attendance.id,
                "client_config_id": client_config.id,
                "state": "pending",
            })
            attendance.write({
                "x_hub_verified": True,
                "x_sync_state": "pending",
                "x_sync_error": False,
            })
        return records

    @api.model
    def create_verified_attendance_from_hub(self, payload):
        allowed = {"employee_id", "device_uuid", "face_token", "faceio_id", "lat", "long"}
        required = ["employee_id", "device_uuid", "lat", "long"]

        extra = sorted(set(payload.keys()) - allowed)
        if extra:
            raise ValidationError(_("Unexpected parameters: %s") % ", ".join(extra))

        missing = [key for key in required if payload.get(key) in (None, "")]
        if missing:
            raise ValidationError(_("Missing required parameters: %s") % ", ".join(missing))

        incoming_faceio_id = payload.get("faceio_id")
        incoming_face_token = payload.get("face_token")
        if not incoming_faceio_id and not incoming_face_token:
            raise ValidationError(_("Either 'faceio_id' or legacy 'face_token' must be provided."))

        employee = self.env["hr.employee"].browse(int(payload["employee_id"]))
        if not employee.exists():
            raise ValidationError(_("Employee not found."))

        employee._check_device_id(payload.get("device_uuid"))
        if incoming_faceio_id:
            employee._verify_faceio_id(incoming_faceio_id)
            config_params = self.env["ir.config_parameter"].sudo()
            if config_params.get_param("pt_hr_hub_server.faceio_enabled"):
                self._verify_faceio_identity_global(incoming_faceio_id)
        else:
            employee._verify_face_token(incoming_face_token)

        employee._check_geofence(payload.get("lat"), payload.get("long"))

        vals = {
            "employee_id": employee.id,
            "check_in": fields.Datetime.now(),
            "x_latitude": float(payload.get("lat")),
            "x_longitude": float(payload.get("long")),
            "x_device_id_used": payload.get("device_uuid"),
        }
        return self.with_context(hub_attendance_verified=True).create([vals])[0]

    def _verify_faceio_identity_global(self, faceio_id):
        """Verify facial ID against global FaceIO API settings."""
        config_params = self.env["ir.config_parameter"].sudo()
        faceio_app_public_id = config_params.get_param("pt_hr_hub_server.faceio_app_public_id")
        faceio_secret_key_encrypted = config_params.get_param("pt_hr_hub_server.faceio_secret_key_encrypted")
        faceio_identity_endpoint = config_params.get_param("pt_hr_hub_server.faceio_identity_endpoint")

        if not faceio_app_public_id or not faceio_secret_key_encrypted:
            raise ValidationError(_("FaceIO credentials are not configured in system settings."))

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
            endpoint = endpoint_template_candidate.format(faceio_id=url_parse.quote(faceio_id, safe=""))
            req = url_request.Request(endpoint, headers=request_headers, method="GET")
            try:
                with url_request.urlopen(req, timeout=15) as response:
                    raw_body = response.read().decode("utf-8")
                break
            except url_error.HTTPError as error:
                message = error.read().decode("utf-8", errors="ignore")
                last_http_error = (error.code, message or error.reason)
                if error.code == 404 and "No such API endpoint" in message:
                    _logger.warning(
                        "FACEIO endpoint %s is not supported by provider (%s). "
                        "Skipping remote identity verification and relying on local employee faceio_id check.",
                        endpoint,
                        message,
                    )
                    continue
                raise ValidationError(_("FaceIO verification failed (%s): %s") % (error.code, message or error.reason))
            except Exception as error:
                raise ValidationError(_("Unable to reach FaceIO verification service: %s") % str(error))

        if not raw_body and last_http_error:
            code, message = last_http_error
            if code == 404 and "No such API endpoint" in str(message or ""):
                return True
            raise ValidationError(_("FaceIO verification failed (%s): %s") % last_http_error)

        if not raw_body:
            raise ValidationError(_("FaceIO verification returned an empty response."))

        try:
            payload = json.loads(raw_body)
        except Exception:
            raise ValidationError(_("FaceIO verification returned an invalid JSON response."))

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

        if faceio_id not in candidates:
            raise ValidationError(_("FaceIO identity response does not match the provided facial ID."))

        return True

    @api.model
    def _get_fernet(self):
        if Fernet is None:
            raise UserError(_("Package 'cryptography' is required."))
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

    @api.model
    def facial_checkin_checkout(self, facial_id, lat=0.0, lng=0.0, device_uuid=None):
        """Find employee by FaceIO facial ID and toggle check-in / check-out.

        Returns a dict with action taken, employee info, and attendance details.
        """
        if not facial_id:
            raise ValidationError(_("Facial ID is required."))

        employee = self.env["hr.employee"].sudo().search(
            [("x_faceio_id", "=", facial_id)], limit=1
        )
        if not employee:
            raise ValidationError(_("No employee found with this facial ID. Please enroll first."))

        employee._check_geofence(lat, lng)

        now = fields.Datetime.now()

        # Find open (unclosed) attendance
        open_attendance = self.sudo().search([
            ("employee_id", "=", employee.id),
            ("check_out", "=", False),
        ], limit=1, order="check_in desc")

        if open_attendance:
            # Check-out
            open_attendance.write({
                "check_out": now,
                "x_latitude": float(lat),
                "x_longitude": float(lng),
            })
            worked_seconds = (now - open_attendance.check_in).total_seconds()
            hours, remainder = divmod(int(worked_seconds), 3600)
            minutes = remainder // 60
            return {
                "action": "check_out",
                "employee_id": employee.id,
                "employee_name": employee.name,
                "employee_job": employee.job_id.name or "",
                "attendance_id": open_attendance.id,
                "check_in": fields.Datetime.to_string(open_attendance.check_in),
                "check_out": fields.Datetime.to_string(now),
                "worked_hours": "%dh %02dm" % (hours, minutes),
            }
        else:
            # Check-in
            attendance = self.with_context(hub_attendance_verified=True).sudo().create([{
                "employee_id": employee.id,
                "check_in": now,
                "x_latitude": float(lat),
                "x_longitude": float(lng),
                "x_device_id_used": device_uuid or "faceio-kiosk",
                "x_hub_verified": True,
            }])[0]
            return {
                "action": "check_in",
                "employee_id": employee.id,
                "employee_name": employee.name,
                "employee_job": employee.job_id.name or "",
                "attendance_id": attendance.id,
                "check_in": fields.Datetime.to_string(now),
                "check_out": False,
                "worked_hours": None,
            }


class HubAttendanceSyncQueue(models.Model):
    _name = "hub.attendance.sync.queue"
    _description = "Hub Attendance Sync Queue"
    _order = "id asc"

    attendance_id = fields.Many2one("hr.attendance", required=True, ondelete="cascade")
    client_config_id = fields.Many2one("hub.client.config", required=True, ondelete="restrict")
    state = fields.Selection(
        selection=[("pending", "Pending"), ("done", "Done"), ("failed", "Failed")],
        default="pending",
        required=True,
        index=True,
    )
    attempt_count = fields.Integer(default=0)
    next_retry_at = fields.Datetime()
    last_error = fields.Text()

    def _next_retry_datetime(self, attempt_count):
        # Exponential backoff in minutes: 1, 2, 4, 8, 16, 32
        delay_minutes = 2 ** min(attempt_count, 5)
        return fields.Datetime.now() + timedelta(minutes=delay_minutes)

    def _sync_to_remote(self):
        self.ensure_one()
        attendance = self.attendance_id
        config = self.client_config_id
        creds = config.get_rpc_credentials()

        common_proxy = xmlrpc.client.ServerProxy("%s/xmlrpc/2/common" % creds["url"], allow_none=True)
        uid = common_proxy.authenticate(creds["db"], creds["user"], creds["api_key"], {})
        if not uid:
            raise UserError(_("Remote authentication failed for client '%s'.") % config.display_name)

        object_proxy = xmlrpc.client.ServerProxy("%s/xmlrpc/2/object" % creds["url"], allow_none=True)
        values = {
            "employee_id": attendance.employee_id.id,
            "check_in": fields.Datetime.to_string(attendance.check_in),
            "x_latitude": attendance.x_latitude,
            "x_longitude": attendance.x_longitude,
            "x_device_id_used": attendance.x_device_id_used,
        }
        if attendance.check_out:
            values["check_out"] = fields.Datetime.to_string(attendance.check_out)

        object_proxy.execute_kw(
            creds["db"],
            uid,
            creds["api_key"],
            "hr.attendance",
            "create",
            [values],
        )

    @api.model
    def _cron_process_pending_sync(self, limit=100):
        now = fields.Datetime.now()
        domain = [
            ("state", "in", ["pending", "failed"]),
            "|",
            ("next_retry_at", "=", False),
            ("next_retry_at", "<=", now),
        ]
        queue_entries = self.search(domain, limit=limit)
        for entry in queue_entries:
            try:
                entry._sync_to_remote()
                entry.write({
                    "state": "done",
                    "last_error": False,
                })
                entry.attendance_id.write({
                    "x_sync_state": "done",
                    "x_sync_error": False,
                })
            except Exception as error:
                new_attempt_count = entry.attempt_count + 1
                entry.write({
                    "state": "failed",
                    "attempt_count": new_attempt_count,
                    "next_retry_at": entry._next_retry_datetime(new_attempt_count),
                    "last_error": str(error),
                })
                entry.attendance_id.write({
                    "x_sync_state": "failed",
                    "x_sync_error": str(error),
                })
                _logger.exception("Attendance sync failed for queue entry %s", entry.id)
