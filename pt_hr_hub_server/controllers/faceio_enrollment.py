# -*- coding: utf-8 -*-

from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request
from werkzeug.exceptions import Forbidden


class HrHubFaceIoEnrollmentController(http.Controller):

    def _ensure_hr_manager(self):
        if not request.env.user.has_group("hr.group_hr_manager"):
            raise Forbidden()

    @http.route("/hr_hub/faceio/enroll", type="http", auth="user")
    def hr_hub_faceio_enroll_page(self, **kw):
        self._ensure_hr_manager()
        params = request.env["ir.config_parameter"].sudo()
        faceio_enabled = str(params.get_param("pt_hr_hub_server.faceio_enabled") or "").lower() in ("1", "true", "yes")
        faceio_app_public_id = params.get_param("pt_hr_hub_server.faceio_app_public_id") or ""
        employees = request.env["hr.employee"].sudo().search([], order="name asc")
        selected_employee_id = 0
        if kw.get("employee_id"):
            try:
                selected_employee_id = int(kw.get("employee_id"))
            except Exception:
                selected_employee_id = 0
        return request.render("pt_hr_hub_server.faceio_enrollment_page", {
            "faceio_enabled": faceio_enabled,
            "faceio_app_public_id": faceio_app_public_id,
            "employees": employees,
            "selected_employee_id": selected_employee_id,
        })

    @http.route("/hr_hub/faceio/save", type="json", auth="user")
    def hr_hub_faceio_save(self, employee_id=None, facial_id=None, device_uuid=None):
        self._ensure_hr_manager()
        if not employee_id:
            raise ValidationError(_("Employee is required."))
        if not facial_id:
            raise ValidationError(_("Facial ID is required."))

        employee = request.env["hr.employee"].sudo().browse(int(employee_id))
        if not employee.exists():
            raise ValidationError(_("Employee not found."))

        values = {"x_faceio_id": facial_id}
        if device_uuid:
            values["x_device_uuid"] = device_uuid

        employee.write(values)
        return {
            "success": True,
            "employee_id": employee.id,
            "employee_name": employee.name,
            "facial_id": facial_id,
        }
