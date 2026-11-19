# -*- coding: utf-8 -*-
from datetime import date, datetime

from pytz import timezone

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
class TestSpecialSchedule(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Calendar = cls.env['resource.calendar']
        # Sunday -> Thursday, as in Saudi Arabia.
        cls.workdays = [6, 0, 1, 2, 3]
        cls.tz = timezone('Asia/Riyadh')
        cls.calendar = Calendar.create({
            'name': "Standard 40h",
            'tz': 'Asia/Riyadh',
            'attendance_ids': _attendances(cls.workdays, 8, 16),
        })
        cls.ramadan_calendar = Calendar.create({
            'name': "Ramadan 30h",
            'tz': 'Asia/Riyadh',
            'attendance_ids': _attendances(cls.workdays, 9, 15),
            'is_special_schedule': True,
            'special_date_from': date(2027, 2, 8),   # Monday
            'special_date_to': date(2027, 3, 9),     # Tuesday
        })
        cls.department = cls.env['hr.department'].create({'name': "Ramadan Department"})
        cls.employee = cls.env['hr.employee'].create({
            'name': "Ramadan Employee",
            'resource_calendar_id': cls.calendar.id,
            'department_id': cls.department.id,
            'tz': 'Asia/Riyadh',
        })

    def _hours(self, day_from, day_to, employee=None):
        """Scheduled hours of the employee from local midnight of day_from
        to local midnight after day_to."""
        employee = employee or self.employee
        start = self.tz.localize(datetime.combine(day_from, datetime.min.time()))
        stop = self.tz.localize(datetime.combine(day_to, datetime.max.time()))
        return employee._get_work_days_data_batch(start, stop, compute_leaves=False)[employee.id]['hours']

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

    def test_calendar_without_resource(self):
        # Without an employee there is no special schedule to pick.
        start = self.tz.localize(datetime(2027, 2, 14))
        stop = self.tz.localize(datetime(2027, 2, 20, 23, 59))
        self.assertEqual(self.calendar.get_work_hours_count(start, stop, compute_leaves=False), 40)

    def test_employee_work_days(self):
        start = self.tz.localize(datetime(2027, 2, 14))
        stop = self.tz.localize(datetime(2027, 2, 18, 23, 59))
        data = self.employee._get_work_days_data_batch(start, stop)[self.employee.id]
        self.assertEqual(data['days'], 5)
        self.assertEqual(data['hours'], 30)

    def test_special_calendar(self):
        self.assertEqual(self.employee._get_special_calendar(date(2027, 2, 20)), self.ramadan_calendar)
        self.assertEqual(self.employee._get_special_calendar(date(2027, 3, 10)), self.calendar)

    def test_other_department(self):
        self.ramadan_calendar.special_department_ids = self.env['hr.department'].create({'name': "Other"})
        self.assertEqual(self._hours(date(2027, 2, 14), date(2027, 2, 20)), 40)
        self.ramadan_calendar.special_department_ids = self.department
        self.assertEqual(self._hours(date(2027, 2, 14), date(2027, 2, 20)), 30)

    def test_archived_special_calendar(self):
        self.ramadan_calendar.active = False
        self.assertEqual(self._hours(date(2027, 2, 14), date(2027, 2, 20)), 40)

    def test_other_company(self):
        self.ramadan_calendar.special_company_ids = self.env['res.company'].create({'name': "Other Company"})
        self.assertEqual(self._hours(date(2027, 2, 14), date(2027, 2, 20)), 40)

    def test_most_specific_wins(self):
        self.env['resource.calendar'].create({
            'name': "Ramadan 25h",
            'tz': 'Asia/Riyadh',
            'attendance_ids': _attendances(self.workdays, 10, 15),
            'is_special_schedule': True,
            'special_date_from': date(2027, 2, 8),
            'special_date_to': date(2027, 3, 9),
            'special_employee_ids': [(6, 0, self.employee.ids)],
        })
        other = self.employee.copy({'name': "Other Employee"})
        self.assertEqual(self._hours(date(2027, 2, 14), date(2027, 2, 20)), 25)
        self.assertEqual(self._hours(date(2027, 2, 14), date(2027, 2, 20), other), 30)

    def test_batch_of_employees(self):
        other = self.env['hr.employee'].create({
            'name': "Other Employee",
            'resource_calendar_id': self.calendar.id,
            'tz': 'Asia/Riyadh',
        })
        self.ramadan_calendar.special_department_ids = self.department
        start = self.tz.localize(datetime(2027, 2, 14))
        stop = self.tz.localize(datetime(2027, 2, 20, 23, 59))
        data = (self.employee | other)._get_work_days_data_batch(start, stop, compute_leaves=False)
        self.assertEqual(data[self.employee.id]['hours'], 30)
        self.assertEqual(data[other.id]['hours'], 40)

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

    # ------------------------------------------------------------
    # Time off start / end hours
    # ------------------------------------------------------------
    def _leave(self, day_from, day_to=None, half=None):
        leave_type = self.env['hr.leave.type'].create({
            'name': "Half Day Test",
            'requires_allocation': 'no',
            'request_unit': 'half_day',
        })
        vals = {
            'employee_id': self.employee.id,
            'holiday_status_id': leave_type.id,
            'request_date_from': day_from,
            'request_date_to': day_to or day_from,
        }
        if half:
            vals.update(request_unit_half=True, request_date_from_period=half)
        return self.env['hr.leave'].new(vals)

    def _local_hours(self, leave):
        to_local = lambda dt: timezone('UTC').localize(dt).astimezone(self.tz)
        start, stop = to_local(leave.date_from), to_local(leave.date_to)
        return (start.hour + start.minute / 60, stop.hour + stop.minute / 60)

    def test_leave_full_day_in_ramadan(self):
        leave = self._leave(date(2027, 2, 15))
        self.assertEqual(self._local_hours(leave), (9, 15))
        self.assertEqual(leave.number_of_hours, 6)

    def test_leave_half_days_in_ramadan(self):
        # A single 09:00-15:00 line: split in two equal halves.
        morning = self._leave(date(2027, 2, 15), half='am')
        afternoon = self._leave(date(2027, 2, 15), half='pm')
        self.assertEqual(self._local_hours(morning), (9, 12))
        self.assertEqual(self._local_hours(afternoon), (12, 15))
        self.assertEqual(morning.number_of_hours, 3)
        self.assertEqual(afternoon.number_of_hours, 3)

    def test_leave_half_days_follow_ramadan_lines(self):
        # Morning / afternoon lines defined by HR are used as they are.
        lines = [(5, 0, 0)]
        for day in self.workdays:
            lines += [
                (0, 0, {'name': 'AM', 'dayofweek': str(day), 'hour_from': 9, 'hour_to': 13, 'day_period': 'morning'}),
                (0, 0, {'name': 'PM', 'dayofweek': str(day), 'hour_from': 13, 'hour_to': 15, 'day_period': 'afternoon'}),
            ]
        self.ramadan_calendar.attendance_ids = lines
        self.assertEqual(self._local_hours(self._leave(date(2027, 2, 15), half='am')), (9, 13))
        self.assertEqual(self._local_hours(self._leave(date(2027, 2, 15), half='pm')), (13, 15))

    def test_leave_outside_ramadan(self):
        leave = self._leave(date(2027, 3, 15))
        self.assertEqual(self._local_hours(leave), (8, 16))
        self.assertEqual(leave.number_of_hours, 8)

    def test_leave_across_start_of_ramadan(self):
        # Sun 2027-02-07 normal (from 08:00) -> Mon 2027-02-08 Ramadan (until 15:00)
        leave = self._leave(date(2027, 2, 7), date(2027, 2, 8))
        self.assertEqual(self._local_hours(leave), (8, 15))
        self.assertEqual(leave.number_of_hours, 8 + 6)

    def test_leave_other_department_unchanged(self):
        self.ramadan_calendar.special_department_ids = self.env['hr.department'].create({'name': "Other"})
        self.assertEqual(self._local_hours(self._leave(date(2027, 2, 15))), (8, 16))
