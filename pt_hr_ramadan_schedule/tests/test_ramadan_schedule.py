# -*- coding: utf-8 -*-
from datetime import date, datetime

from pytz import timezone

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, freeze_time, tagged


def _attendances(days, hour_from, hour_to):
    return [(5, 0, 0)] + [
        (0, 0, {
            'name': str(day),
            'dayofweek': str(day),
            'hour_from': hour_from,
            'hour_to': hour_to,
            'day_period': 'morning',
        }) for day in days
    ]


@tagged('post_install', '-at_install')
class TestRamadanSchedule(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Calendar = cls.env['resource.calendar']
        # Sunday -> Thursday, as in Saudi Arabia.
        workdays = [6, 0, 1, 2, 3]
        cls.tz = timezone('Asia/Riyadh')
        cls.ramadan_calendar = Calendar.create({
            'name': "Ramadan 30h",
            'tz': 'Asia/Riyadh',
            'attendance_ids': _attendances(workdays, 9, 15),
        })
        cls.calendar = Calendar.create({
            'name': "Standard 40h",
            'tz': 'Asia/Riyadh',
            'attendance_ids': _attendances(workdays, 8, 16),
            'ramadan_calendar_id': cls.ramadan_calendar.id,
        })
        cls.period = cls.env['hr.ramadan.period'].create({
            'name': "Ramadan 1448",
            'date_start': date(2027, 2, 8),   # Monday
            'date_end': date(2027, 3, 9),     # Tuesday
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': "Ramadan Employee",
            'resource_calendar_id': cls.calendar.id,
            'tz': 'Asia/Riyadh',
        })

    def _hours(self, day_from, day_to, calendar=None):
        """Scheduled hours from local midnight of day_from to local
        midnight after day_to."""
        start = self.tz.localize(datetime.combine(day_from, datetime.min.time()))
        stop = self.tz.localize(datetime.combine(day_to, datetime.max.time()))
        return (calendar or self.calendar).get_work_hours_count(start, stop, compute_leaves=False)

    def test_normal_week(self):
        # Sun 2027-01-24 -> Sat 2027-01-30
        self.assertEqual(self._hours(date(2027, 1, 24), date(2027, 1, 30)), 40)

    def test_ramadan_week(self):
        # Sun 2027-02-14 -> Sat 2027-02-20
        self.assertEqual(self._hours(date(2027, 2, 14), date(2027, 2, 20)), 30)

    def test_week_across_start_of_ramadan(self):
        # Sun 2027-02-07 (normal, 8h) + Mon->Thu 2027-02-08..11 (Ramadan, 4x6h)
        self.assertEqual(self._hours(date(2027, 2, 7), date(2027, 2, 13)), 8 + 4 * 6)

    def test_week_across_end_of_ramadan(self):
        # Sun 2027-03-07 -> Tue 2027-03-09 Ramadan (3x6h), Wed-Thu normal (2x8h)
        self.assertEqual(self._hours(date(2027, 3, 7), date(2027, 3, 13)), 3 * 6 + 2 * 8)

    def test_shift_hours_in_ramadan(self):
        start = self.tz.localize(datetime(2027, 2, 15))
        stop = self.tz.localize(datetime(2027, 2, 16))
        resource = self.employee.resource_id
        intervals = list(self.calendar._attendance_intervals_batch(start, stop, resource)[resource.id])
        self.assertEqual([(i[0].hour, i[1].hour) for i in intervals], [(9, 15)])

    def test_employee_work_days(self):
        start = self.tz.localize(datetime(2027, 2, 14))
        stop = self.tz.localize(datetime(2027, 2, 18, 23, 59))
        data = self.employee._get_work_days_data_batch(start, stop)[self.employee.id]
        self.assertEqual(data['days'], 5)
        self.assertEqual(data['hours'], 30)

    def test_effective_calendar(self):
        self.assertEqual(self.calendar._get_effective_calendar(date(2027, 2, 20)), self.ramadan_calendar)
        self.assertEqual(self.calendar._get_effective_calendar(date(2027, 3, 10)), self.calendar)
        self.assertEqual(self.ramadan_calendar._get_effective_calendar(date(2027, 2, 20)), self.ramadan_calendar)

    def test_calendar_without_ramadan_schedule(self):
        self.calendar.ramadan_calendar_id = False
        self.assertEqual(self._hours(date(2027, 2, 14), date(2027, 2, 20)), 40)

    def test_archived_period(self):
        self.period.active = False
        self.assertEqual(self._hours(date(2027, 2, 14), date(2027, 2, 20)), 40)

    def test_other_company_period(self):
        other_company = self.env['res.company'].create({'name': "Other Company"})
        self.period.company_id = other_company
        self.calendar.company_id = self.env.company
        self.assertEqual(self._hours(date(2027, 2, 14), date(2027, 2, 20)), 40)

    def test_overlapping_periods(self):
        with self.assertRaises(ValidationError):
            self.env['hr.ramadan.period'].create({
                'name': "Overlap",
                'date_start': date(2027, 3, 1),
                'date_end': date(2027, 3, 20),
            })

    def test_ramadan_schedule_constraints(self):
        with self.assertRaises(ValidationError):
            self.calendar.ramadan_calendar_id = self.calendar
        with self.assertRaises(ValidationError):
            self.ramadan_calendar.ramadan_calendar_id = self.calendar

    @freeze_time('2027-02-15 08:00:00')  # 11:00 in Riyadh, during Ramadan
    def test_mobile_app_shift(self):
        if 'employee_mobile' not in self.env.registry._init_modules:
            self.skipTest("employee_mobile is not installed")
        from odoo.addons.employee_mobile.controllers.main import _build_shift
        self.assertEqual(_build_shift(self.employee), {
            'name': "Ramadan 30h",
            'start': '09:00',
            'end': '15:00',
        })
