# -*- coding: utf-8 -*-

import logging

from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request
from werkzeug.exceptions import Forbidden

_logger = logging.getLogger(__name__)


class HrHubFaceIoAttendanceController(http.Controller):

    def _faceio_config(self):
        params = request.env["ir.config_parameter"].sudo()
        return {
            "enabled": str(params.get_param("pt_hr_hub_server.faceio_enabled") or "").lower() in ("1", "true", "yes"),
            "app_public_id": params.get_param("pt_hr_hub_server.faceio_app_public_id") or "",
        }

    @http.route("/hr_hub/faceio/kiosk", type="http", auth="user")
    def faceio_kiosk_page(self, **kw):
        if not request.env.user.has_group("hr.group_hr_user"):
            raise Forbidden()
        cfg = self._faceio_config()
        return request.render("pt_hr_hub_server.faceio_kiosk_page", {
            "faceio_enabled": cfg["enabled"],
            "faceio_app_public_id": cfg["app_public_id"],
        })

    @http.route("/hr_hub/faceio/kiosk/checkin", type="json", auth="user")
    def faceio_kiosk_checkin(self, facial_id=None, lat=0.0, lng=0.0, device_uuid=None):
        if not request.env.user.has_group("hr.group_hr_user"):
            raise Forbidden()
        if not facial_id:
            raise ValidationError(_("Facial ID is required."))
        try:
            result = request.env["hr.attendance"].sudo().facial_checkin_checkout(
                facial_id=facial_id,
                lat=float(lat or 0),
                lng=float(lng or 0),
                device_uuid=device_uuid,
            )
            return result
        except ValidationError as e:
            raise ValidationError(str(e))
        except Exception as e:
            _logger.exception("Facial kiosk check-in error")
            raise ValidationError(_("Unexpected error: %s") % str(e))
