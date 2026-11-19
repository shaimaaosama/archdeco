# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import datetime, time, timedelta

from pytz import timezone

from odoo import _, models


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    def _get_special_segments(self, employee, start_dt, end_dt, local_tz, special_calendars):
        """Split [start_dt, end_dt) into (start, end, calendar) segments, one
        per run of local days applying the same schedule to ``employee``.
        Empty when no special schedule applies to it in the range."""
        self.ensure_one()
        # Cheap pre-filter: special schedules whose filters match the employee.
        special_calendars = special_calendars.filtered(
            lambda c: employee._get_special_calendar(c.special_date_from, self, c) == c)
        if not special_calendars:
            return ()
        segments = []
        day = start_dt.astimezone(local_tz).date()
        last_day = end_dt.astimezone(local_tz).date()
        while day <= last_day:
            calendar = employee._get_special_calendar(day, self, special_calendars).with_env(self.env)
            # Special schedule days start and end at local midnight.
            day_start = max(local_tz.localize(datetime.combine(day, time.min)), start_dt)
            day_end = min(local_tz.localize(datetime.combine(day + timedelta(days=1), time.min)), end_dt)
            if day_start < day_end:
                if segments and segments[-1][2] == calendar:
                    segments[-1] = (segments[-1][0], day_end, calendar)
                else:
                    segments.append((day_start, day_end, calendar))
            day += timedelta(days=1)
        if all(calendar == self for _start, _end, calendar in segments):
            return ()
        return tuple(segments)

    def _attendance_intervals_batch(self, start_dt, end_dt, resources=None, domain=None, tz=None, lunch=False):
        result = super()._attendance_intervals_batch(
            start_dt, end_dt, resources=resources, domain=domain, tz=tz, lunch=lunch)
        # Special schedules depend on the employee: nothing to replace without
        # resources, or when computing a special schedule / a segment itself.
        if not resources or self.is_special_schedule or self.env.context.get('skip_special_schedule'):
            return result

        # sudo: schedules are evaluated for users without HR rights too
        # (employees requesting time off, the mobile app...). One extra day on
        # each side covers timezone shifts.
        special_calendars = self.env['resource.calendar'].sudo()._get_special_calendars(
            (start_dt - timedelta(days=1)).date(), (end_dt + timedelta(days=1)).date())
        if not special_calendars:
            return result
        employees = self.env['hr.employee'].sudo().with_context(active_test=False).search(
            [('resource_id', 'in', resources.ids)])
        employee_per_resource = {employee.resource_id.id: employee for employee in employees}

        # Resources with the same segments are computed together.
        resources_per_segments = defaultdict(lambda: self.env['resource.resource'])
        for resource in resources:
            employee = employee_per_resource.get(resource.id)
            if not employee:
                continue
            local_tz = tz or timezone(resource.tz or self.tz or 'UTC')
            segments = self._get_special_segments(employee, start_dt, end_dt, local_tz, special_calendars)
            if segments:
                resources_per_segments[segments] |= resource

        for segments, segment_resources in resources_per_segments.items():
            intervals = {}
            for seg_start, seg_end, calendar in segments:
                calendar = calendar.with_context(skip_special_schedule=True)
                seg_result = calendar._attendance_intervals_batch(
                    seg_start, seg_end, resources=segment_resources, domain=domain, tz=tz, lunch=lunch)
                for resource in segment_resources:
                    seg_intervals = seg_result[resource.id]
                    intervals[resource.id] = intervals[resource.id] | seg_intervals if resource.id in intervals else seg_intervals
            result.update(intervals)
        return result

    def action_recompute_attendance_overtime(self):
        """Recompute attendance overtime of the special schedule's days,
        needed when it is created or changed after attendances were already
        recorded."""
        Attendance = self.env['hr.attendance'].sudo()
        for calendar in self.filtered('is_special_schedule'):
            # One extra day on each side covers timezone shifts.
            start = datetime.combine(calendar.special_date_from - timedelta(days=1), time.min)
            stop = datetime.combine(calendar.special_date_to + timedelta(days=2), time.min)
            domain = [('check_in', '>=', start), ('check_in', '<', stop)]
            if calendar.special_company_ids:
                domain.append(('employee_id.company_id', 'in', calendar.special_company_ids.ids))
            Attendance.search(domain)._update_overtime()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _("Attendance overtime recomputed."),
            },
        }
