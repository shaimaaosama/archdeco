# -*- coding: utf-8 -*-
from odoo import models


class AttendanceSheet(models.Model):
    _inherit = 'attendance.sheet'

    def get_attendances(self):
        for sheet in self:
            super(AttendanceSheet, sheet.with_context(
                special_schedule_employee_id=sheet.employee_id.id)).get_attendances()
