# -*- coding: utf-8 -*-
from odoo import models


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    def _get_hour_from_to(self, request_date_from, request_date_to, day_period=None):
        # Odoo reads the start / end hours of a time off (and of each half day)
        # from the schedule lines directly, not through
        # _attendance_intervals_batch: take them from the special schedule
        # applied to the employee on each of the two days.
        self.ensure_one()
        calendar = self.resource_calendar_id
        employee = self.employee_id.sudo()
        if not employee or not calendar or calendar.is_special_schedule:
            return super()._get_hour_from_to(request_date_from, request_date_to, day_period=day_period)
        calendar_from = employee._get_special_calendar(request_date_from, calendar)
        calendar_to = employee._get_special_calendar(request_date_to, calendar)
        if calendar_from == calendar and calendar_to == calendar:
            return super()._get_hour_from_to(request_date_from, request_date_to, day_period=day_period)
        hour_from = self._get_special_hour_from_to(calendar_from, request_date_from, day_period)[0]
        hour_to = self._get_special_hour_from_to(calendar_to, request_date_to, day_period)[1]
        return hour_from, hour_to

    def _get_special_hour_from_to(self, calendar, day, day_period):
        """(hour_from, hour_to) of ``day`` in ``calendar``. A half day of a
        special schedule without both a morning and an afternoon line on that
        day (e.g. a single 09:00-15:00 Ramadan line) is half of its hours."""
        lines = calendar.attendance_ids.filtered(
            lambda a: not a.display_type and a.day_period != 'lunch' and int(a.dayofweek) == day.weekday())
        if calendar.two_weeks_calendar:
            week_type = self.env['resource.calendar.attendance'].get_week_type(day)
            lines = lines.filtered(lambda a: int(a.week_type) == week_type)
        if day_period and lines and set(lines.mapped('day_period')) != {'morning', 'afternoon'}:
            start = min(lines.mapped('hour_from'))
            end = max(lines.mapped('hour_to'))
            middle = (start + end) / 2
            return (start, middle) if day_period == 'morning' else (middle, end)
        leave = self.new({'resource_calendar_id': calendar.id})
        return super(HrLeave, leave)._get_hour_from_to(day, day, day_period=day_period)
