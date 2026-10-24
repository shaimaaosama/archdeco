# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta

from pytz import timezone

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    ramadan_calendar_id = fields.Many2one(
        'resource.calendar', string="Ramadan Schedule",
        domain="[('id', '!=', id), ('ramadan_calendar_id', '=', False), "
               "('company_id', 'in', [company_id, False])]",
        help="Working schedule applied instead of this one during the "
             "Ramadan periods (Employees > Configuration > Ramadan Periods).")

    @api.constrains('ramadan_calendar_id')
    def _check_ramadan_calendar_id(self):
        for calendar in self.filtered('ramadan_calendar_id'):
            if calendar.ramadan_calendar_id == calendar:
                raise ValidationError(_(
                    "A working schedule cannot be its own Ramadan schedule."))
            if calendar.ramadan_calendar_id.ramadan_calendar_id:
                raise ValidationError(_(
                    "The Ramadan schedule %(ramadan)s has a Ramadan schedule "
                    "itself.", ramadan=calendar.ramadan_calendar_id.name))

    def _get_ramadan_periods(self, date_from, date_to):
        """Active Ramadan periods of this calendar's company overlapping
        [date_from, date_to] (dates, inclusive)."""
        self.ensure_one()
        company_ids = [False, (self.company_id or self.env.company).id]
        # sudo: schedules are evaluated for users without HR rights too
        # (employees requesting time off, the mobile app...).
        return self.env['hr.ramadan.period'].sudo().search([
            ('company_id', 'in', company_ids),
            ('date_start', '<=', date_to),
            ('date_end', '>=', date_from),
        ], order='date_start')

    def _get_effective_calendar(self, day):
        """The calendar actually applied on ``day``: the Ramadan schedule
        during a Ramadan period, this calendar otherwise."""
        self.ensure_one()
        if self.ramadan_calendar_id and self._get_ramadan_periods(day, day):
            return self.ramadan_calendar_id
        return self

    def _attendance_intervals_batch(self, start_dt, end_dt, resources=None, domain=None, tz=None, lunch=False):
        if not self.ramadan_calendar_id or self.env.context.get('skip_ramadan_schedule'):
            return super()._attendance_intervals_batch(
                start_dt, end_dt, resources=resources, domain=domain, tz=tz, lunch=lunch)

        # Ramadan days start and end at local midnight.
        local_tz = tz or timezone(self.tz or 'UTC')
        periods = self._get_ramadan_periods(
            start_dt.astimezone(local_tz).date(), end_dt.astimezone(local_tz).date())
        if not periods:
            return super()._attendance_intervals_batch(
                start_dt, end_dt, resources=resources, domain=domain, tz=tz, lunch=lunch)

        # Split [start_dt, end_dt) into normal and Ramadan segments.
        segments = []
        cursor = start_dt
        for period in periods:
            ramadan_start = local_tz.localize(datetime.combine(period.date_start, time.min))
            ramadan_end = local_tz.localize(datetime.combine(period.date_end + timedelta(days=1), time.min))
            ramadan_start, ramadan_end = max(ramadan_start, cursor), min(ramadan_end, end_dt)
            if ramadan_start >= ramadan_end:
                continue
            if cursor < ramadan_start:
                segments.append((cursor, ramadan_start, self))
            segments.append((ramadan_start, ramadan_end, self.ramadan_calendar_id))
            cursor = ramadan_end
        if cursor < end_dt:
            segments.append((cursor, end_dt, self))

        result = {}
        for seg_start, seg_end, calendar in segments:
            calendar = calendar.with_context(skip_ramadan_schedule=True)
            seg_result = calendar._attendance_intervals_batch(
                seg_start, seg_end, resources=resources, domain=domain, tz=tz, lunch=lunch)
            for resource_id, intervals in seg_result.items():
                result[resource_id] = result[resource_id] | intervals if resource_id in result else intervals
        return result
