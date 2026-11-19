# -*- coding: utf-8 -*-
from odoo import models


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    def _get_day_attendances(self, day_date, start_time, end_time):
        # The attendance sheet reads the schedule lines directly instead of
        # going through _attendance_intervals_batch, and without the employee:
        # the sheet passes it in the context.
        employee_id = self.env.context.get('special_schedule_employee_id')
        if employee_id and not self.is_special_schedule:
            employee = self.env['hr.employee'].sudo().browse(employee_id)
            calendar = employee._get_special_calendar(day_date, self).with_env(self.env)
            if calendar != self:
                return calendar._get_day_attendances(day_date, start_time, end_time)
        return super()._get_day_attendances(day_date, start_time, end_time)
