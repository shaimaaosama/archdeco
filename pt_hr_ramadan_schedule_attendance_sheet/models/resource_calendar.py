# -*- coding: utf-8 -*-
from odoo import models


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    def _get_day_attendances(self, day_date, start_time, end_time):
        # The attendance sheet reads the schedule lines directly instead of
        # going through _attendance_intervals_batch.
        calendar = self._get_effective_calendar(day_date)
        if calendar != self:
            return calendar._get_day_attendances(day_date, start_time, end_time)
        return super()._get_day_attendances(day_date, start_time, end_time)
