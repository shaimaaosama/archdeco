# -*- coding: utf-8 -*-

import logging

from odoo import http
from odoo.http import request
from odoo.addons.muk_rest import core
from odoo.addons.muk_rest.tools.http import build_route

_logger = logging.getLogger(__name__)


class HrAttendanceHubController(http.Controller):
    def _create_attendance(self, payload):
        attendance = request.env["hr.attendance"].sudo().create_verified_attendance_from_hub(payload)
        return {
            "success": True,
            "attendance_id": attendance.id,
            "sync_state": attendance.x_sync_state,
        }

    @core.http.rest_route(
        routes=build_route("/hr_hub/attendance"),
        methods=["POST"],
        protected=True,
        docs={
            "tags": ["HR Hub"],
            "summary": "Create Attendance",
            "description": "Validate device and facial proof (faceio_id, or legacy face_token), enforce employee geo fence when enabled, and create attendance entry.",
        },
    )
    def post_hr_hub_attendance(self, **kw):
        payload = kw or request.params
        return request.make_json_response(self._create_attendance(payload))
