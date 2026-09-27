# -*- coding: utf-8 -*-
import hashlib
import json
from datetime import timedelta

from odoo import fields
from odoo.tests import HttpCase, tagged

COMPANY_LAT = 24.7136
COMPANY_LON = 46.6753
WL_LAT = 24.8000
WL_LON = 46.7000
FAR_LAT = 25.2048
FAR_LON = 55.2708  # Dubai: far from everything above


@tagged('post_install', '-at_install')
class TestMobileApi(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Employee = cls.env['hr.employee']
        Company = cls.env['res.company']

        cls.company = cls.env.company
        cls.company.write({
            'attendance_latitude': COMPANY_LAT,
            'attendance_longitude': COMPANY_LON,
            'attendance_radius': 100.0,
            'mobile_late_grace_minutes': 5,
            'mobile_block_mock_location': True,
        })

        cls.calendar = cls.env['resource.calendar'].create({
            'name': 'Mobile Test Calendar',
            'tz': 'Asia/Riyadh',
            'company_id': cls.company.id,
            'hours_per_day': 8.0,
            'attendance_ids': [
                (0, 0, {'name': '%s Morning' % day_name, 'dayofweek': str(idx),
                        'hour_from': 8, 'hour_to': 17, 'day_period': 'morning'})
                for idx, day_name in enumerate(
                    ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])
            ],
        })

        cls.work_location = cls.env['hr.work.location'].create({
            'name': 'HQ Site',
            'company_id': cls.company.id,
            'address_id': cls.company.partner_id.id,
            'attendance_latitude': WL_LAT,
            'attendance_longitude': WL_LON,
            'attendance_radius': 100.0,
        })

        cls.emp_wl = Employee.create({
            'name': 'Employee WorkLocation',
            'work_email': 'wl.employee@example.com',
            'pin': '1234',
            'company_id': cls.company.id,
            'resource_calendar_id': cls.calendar.id,
            'tz': 'Asia/Riyadh',
            'work_location_id': cls.work_location.id,
            'mobile_attendance_restriction': 'work_location',
            'mobile_app_access': True,
        })
        cls.emp_company = Employee.create({
            'name': 'Employee Company',
            'work_email': 'company.employee@example.com',
            'pin': '1234',
            'company_id': cls.company.id,
            'resource_calendar_id': cls.calendar.id,
            'tz': 'Asia/Riyadh',
            'mobile_attendance_restriction': 'company',
            'mobile_app_access': True,
        })
        cls.emp_none = Employee.create({
            'name': 'Employee None',
            'work_email': 'none.employee@example.com',
            'pin': '1234',
            'company_id': cls.company.id,
            'resource_calendar_id': cls.calendar.id,
            'tz': 'Asia/Riyadh',
            'mobile_attendance_restriction': 'none',
            'mobile_app_access': True,
        })
        cls.emp_no_location = Employee.create({
            'name': 'Employee No Location Configured',
            'work_email': 'nolocation.employee@example.com',
            'pin': '1234',
            'company_id': cls.company.id,
            'resource_calendar_id': cls.calendar.id,
            'tz': 'Asia/Riyadh',
            'mobile_attendance_restriction': 'work_location',
            'work_location_id': False,
            'mobile_app_access': True,
        })
        cls.emp_disabled = Employee.create({
            'name': 'Employee Disabled',
            'work_email': 'disabled.employee@example.com',
            'pin': '1234',
            'company_id': cls.company.id,
            'mobile_attendance_restriction': 'none',
            'mobile_app_access': False,
        })

        # -- Payslip (built directly with line_ids, per the plan) --------
        cat_basic = cls.env.ref('hr_payroll.BASIC')
        cat_alw = cls.env.ref('hr_payroll.ALW')
        cat_ded = cls.env.ref('hr_payroll.DED')
        cat_gross = cls.env.ref('hr_payroll.GROSS')
        cat_net = cls.env.ref('hr_payroll.NET')

        struct_type = cls.env['hr.payroll.structure.type'].create({'name': 'Mobile Test Type'})
        struct = cls.env['hr.payroll.structure'].create({
            'name': 'Mobile Test Structure', 'type_id': struct_type.id,
            # Otherwise hr.payslip._compute_worked_days_line_ids() regenerates
            # worked_days_line_ids from real work entries and wipes the
            # manually-created WORK100 line below.
            'use_worked_day_lines': False,
        })
        rules = {}
        for code, cat in (('BASIC', cat_basic), ('ALW1', cat_alw), ('DED1', cat_ded),
                           ('GROSS', cat_gross), ('NET', cat_net)):
            rules[code] = cls.env['hr.salary.rule'].create({
                'name': code, 'code': code, 'category_id': cat.id,
                'struct_id': struct.id, 'sequence': 10,
                'amount_select': 'fix', 'amount_fix': 0.0,
            })

        cls.contract = cls.env['hr.contract'].create({
            'name': 'Mobile Test Contract',
            'employee_id': cls.emp_wl.id,
            'company_id': cls.company.id,
            'wage': 5000.0,
            'state': 'open',
            'date_start': fields.Date.to_date('2026-08-01'),
        })

        cls.payslip = cls.env['hr.payslip'].with_context(
            default_date_from='2026-08-01', default_date_to='2026-08-31',
        ).create({
            'name': 'Mobile Test Payslip - August 2026',
            'employee_id': cls.emp_wl.id,
            'contract_id': cls.contract.id,
            'struct_id': struct.id,
            'state': 'done',
            'paid_date': '2026-09-01',
        })

        cls.env['hr.payslip.line'].create([
            {'slip_id': cls.payslip.id, 'name': 'Basic Salary', 'code': 'BASIC',
             'salary_rule_id': rules['BASIC'].id, 'contract_id': cls.contract.id,
             'employee_id': cls.emp_wl.id, 'total': 5000.0},
            {'slip_id': cls.payslip.id, 'name': 'Allowance', 'code': 'ALW1',
             'salary_rule_id': rules['ALW1'].id, 'contract_id': cls.contract.id,
             'employee_id': cls.emp_wl.id, 'total': 500.0},
            {'slip_id': cls.payslip.id, 'name': 'Deduction', 'code': 'DED1',
             'salary_rule_id': rules['DED1'].id, 'contract_id': cls.contract.id,
             'employee_id': cls.emp_wl.id, 'total': -300.0},
            {'slip_id': cls.payslip.id, 'name': 'Gross', 'code': 'GROSS',
             'salary_rule_id': rules['GROSS'].id, 'contract_id': cls.contract.id,
             'employee_id': cls.emp_wl.id, 'total': 5500.0},
            {'slip_id': cls.payslip.id, 'name': 'Net', 'code': 'NET',
             'salary_rule_id': rules['NET'].id, 'contract_id': cls.contract.id,
             'employee_id': cls.emp_wl.id, 'total': 5200.0},
        ])
        work_entry_attendance = cls.env.ref('hr_work_entry.work_entry_type_attendance')
        cls.env['hr.payslip.worked_days'].create({
            'payslip_id': cls.payslip.id,
            'work_entry_type_id': work_entry_attendance.id,
            'number_of_days': 22.0,
            'number_of_hours': 176.0,
        })
        cls.payslip.flush_recordset()

    # ------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------
    def _call(self, method, path, token=None, body=None, lang=None):
        url = '/api/mobile' + path
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer %s' % token
        if lang:
            headers['Accept-Language'] = lang
        if method == 'GET':
            resp = self.url_open(url, headers=headers)
        else:
            resp = self.url_open(url, data=json.dumps(body or {}).encode('utf-8'), headers=headers)
        return resp

    def _login(self, email, pin, device=None):
        resp = self._call('POST', '/login', body={
            'email': email, 'pin': pin,
            'device': device or {'id': 'dev-1', 'name': 'Test Phone', 'platform': 'android', 'app_version': '1.0.0'},
        })
        return resp

    def _token_for(self, email, pin='1234'):
        resp = self._login(email, pin)
        self.assertEqual(resp.status_code, 200, resp.text)
        return resp.json()['data']['token']

    def _make_expired_token(self, employee):
        raw = 'expired-raw-token-%s' % employee.id
        token_hash = hashlib.sha256(raw.encode('utf-8')).hexdigest()
        self.env['hr.employee.mobile.token'].sudo().create({
            'employee_id': employee.id,
            'token_hash': token_hash,
            'expires_at': fields.Datetime.now() - timedelta(days=1),
            'active': True,
        })
        return raw

    # ------------------------------------------------------------
    # ping
    # ------------------------------------------------------------
    def test_ping(self):
        resp = self._call('GET', '/ping')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['data']['ok'])
        self.assertEqual(data['data']['version'], '18.0.1.0.0')

    # ------------------------------------------------------------
    # login
    # ------------------------------------------------------------
    def test_login_ok(self):
        resp = self._login('wl.employee@example.com', '1234')
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()['data']
        self.assertTrue(data['token'])
        self.assertTrue(data['expires_at'])
        self.assertEqual(data['employee']['work_email'], 'wl.employee@example.com')
        self.assertEqual(data['employee']['attendance_restriction'], 'work_location')

    def test_login_wrong_pin(self):
        resp = self._login('company.employee@example.com', '9999')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['error']['code'], 'INVALID_CREDENTIALS')

    def test_login_unknown_email_same_code(self):
        resp = self._login('nobody@example.com', '1234')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['error']['code'], 'INVALID_CREDENTIALS')

    def test_login_lockout_after_max_attempts(self):
        employee = self.env['hr.employee'].create({
            'name': 'Lockout Target',
            'work_email': 'lockout.target@example.com',
            'pin': '1234',
            'company_id': self.company.id,
            'mobile_attendance_restriction': 'none',
        })
        last_resp = None
        for _i in range(5):
            last_resp = self._login(employee.work_email, '0000')
        self.assertEqual(last_resp.status_code, 429, last_resp.text)
        body = last_resp.json()
        self.assertEqual(body['error']['code'], 'ACCOUNT_LOCKED')
        self.assertIn('retry_after_seconds', body['error']['details'])

        # Even the correct PIN is rejected while locked.
        resp = self._login(employee.work_email, '1234')
        self.assertEqual(resp.status_code, 429)
        self.assertEqual(resp.json()['error']['code'], 'ACCOUNT_LOCKED')

    def test_login_access_disabled(self):
        resp = self._login('disabled.employee@example.com', '1234')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['error']['code'], 'INVALID_CREDENTIALS')

    def test_login_duplicate_work_email_across_companies(self):
        # work_email is not unique across companies; two employees (e.g. in a
        # multi-company setup) can legitimately share one. Login must
        # disambiguate by PIN and log in as the one whose PIN matches.
        company2 = self.env['res.company'].create({'name': 'Second Co'})
        emp_a = self.env['hr.employee'].create({
            'name': 'Dup A',
            'work_email': 'dup.email@example.com',
            'pin': '1111',
            'company_id': self.company.id,
            'mobile_attendance_restriction': 'none',
        })
        emp_b = self.env['hr.employee'].create({
            'name': 'Dup B',
            'work_email': 'dup.email@example.com',
            'pin': '2222',
            'company_id': company2.id,
            'mobile_attendance_restriction': 'none',
        })

        resp = self._login('dup.email@example.com', '1111')
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()['data']['employee']['id'], emp_a.id)

        resp = self._login('dup.email@example.com', '2222')
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()['data']['employee']['id'], emp_b.id)

        # A PIN that matches neither: still the plain, indistinguishable
        # INVALID_CREDENTIALS (never hints which of the two employees it is).
        resp = self._login('dup.email@example.com', '9999')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['error']['code'], 'INVALID_CREDENTIALS')

    # ------------------------------------------------------------
    # tokens
    # ------------------------------------------------------------
    def test_token_missing(self):
        resp = self._call('GET', '/profile')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['error']['code'], 'TOKEN_MISSING')

    def test_token_invalid(self):
        resp = self._call('GET', '/profile', token='not-a-real-token')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['error']['code'], 'TOKEN_INVALID')

    def test_token_expired(self):
        raw = self._make_expired_token(self.emp_none)
        resp = self._call('GET', '/profile', token=raw)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['error']['code'], 'TOKEN_INVALID')

    def test_logout_revokes_token(self):
        token = self._token_for('none.employee@example.com')
        resp = self._call('POST', '/logout', token=token)
        self.assertEqual(resp.status_code, 200, resp.text)

        resp = self._call('GET', '/profile', token=token)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['error']['code'], 'TOKEN_INVALID')

    def test_pin_change_by_hr_revokes_token(self):
        employee = self.env['hr.employee'].create({
            'name': 'HR Revoke Target',
            'work_email': 'hr.revoke@example.com',
            'pin': '1234',
            'company_id': self.company.id,
            'mobile_attendance_restriction': 'none',
        })
        token = self._token_for(employee.work_email)
        resp = self._call('GET', '/profile', token=token)
        self.assertEqual(resp.status_code, 200)

        # HR edits the employee directly (no context key) -> token must be revoked.
        employee.write({'pin': '5678'})

        resp = self._call('GET', '/profile', token=token)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['error']['code'], 'TOKEN_INVALID')

    def test_change_pin_keeps_current_token_revokes_others(self):
        employee = self.env['hr.employee'].create({
            'name': 'Change Pin Target',
            'work_email': 'change.pin@example.com',
            'pin': '1234',
            'company_id': self.company.id,
            'mobile_attendance_restriction': 'none',
        })
        token_a = self._token_for(employee.work_email)
        token_b = self._token_for(employee.work_email)

        resp = self._call('POST', '/change-pin', token=token_a,
                           body={'current_pin': '1234', 'new_pin': '4321'})
        self.assertEqual(resp.status_code, 200, resp.text)

        # token_a (the one used to change the pin) stays valid.
        resp = self._call('GET', '/profile', token=token_a)
        self.assertEqual(resp.status_code, 200)

        # token_b (a different session) is revoked.
        resp = self._call('GET', '/profile', token=token_b)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['error']['code'], 'TOKEN_INVALID')

    def test_change_pin_wrong_current(self):
        token = self._token_for('company.employee@example.com')
        resp = self._call('POST', '/change-pin', token=token,
                           body={'current_pin': '0000', 'new_pin': '4321'})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error']['code'], 'PIN_INCORRECT')

    def test_change_pin_bad_format(self):
        employee = self.env['hr.employee'].create({
            'name': 'Pin Format Target',
            'work_email': 'pin.format@example.com',
            'pin': '1234',
            'company_id': self.company.id,
            'mobile_attendance_restriction': 'none',
        })
        token = self._token_for(employee.work_email)
        resp = self._call('POST', '/change-pin', token=token,
                           body={'current_pin': '1234', 'new_pin': '12'})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error']['code'], 'PIN_FORMAT')

        resp = self._call('POST', '/change-pin', token=token,
                           body={'current_pin': '1234', 'new_pin': '1234'})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error']['code'], 'PIN_FORMAT')

    # ------------------------------------------------------------
    # attendance / check-in / check-out
    # ------------------------------------------------------------
    def test_checkin_inside_fence_writes_core_and_shared_fields(self):
        token = self._token_for('wl.employee@example.com')
        resp = self._call('POST', '/attendance/check-in', token=token, body={
            'latitude': WL_LAT, 'longitude': WL_LON, 'accuracy': 5.0, 'is_mocked': False,
        })
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()['data']
        self.assertEqual(data['attendance']['state'], 'checked_in')
        self.assertAlmostEqual(data['distance'], 0.0, delta=1.0)

        att = self.env['hr.attendance'].sudo().search(
            [('employee_id', '=', self.emp_wl.id)], order='id desc', limit=1)
        self.assertAlmostEqual(att.in_latitude, WL_LAT, places=5)
        self.assertAlmostEqual(att.in_longitude, WL_LON, places=5)
        self.assertAlmostEqual(att.check_in_latitude, WL_LAT, places=5)
        self.assertAlmostEqual(att.check_in_longitude, WL_LON, places=5)
        self.assertEqual(att.in_mode, 'mobile')

        # Check-out (shift check_in back so worked_hours is unambiguously > 0).
        att.write({'check_in': fields.Datetime.now() - timedelta(minutes=30)})
        resp = self._call('POST', '/attendance/check-out', token=token, body={
            'latitude': WL_LAT, 'longitude': WL_LON, 'accuracy': 5.0, 'is_mocked': False,
        })
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()['data']
        self.assertEqual(data['attendance']['state'], 'checked_out')
        self.assertGreater(data['attendance']['today_worked_hours'], 0)
        att.invalidate_recordset()
        self.assertAlmostEqual(att.out_latitude, WL_LAT, places=5)
        self.assertAlmostEqual(att.check_out_latitude, WL_LAT, places=5)
        self.assertGreater(att.worked_hours, 0)

    def test_checkin_outside_fence(self):
        token = self._token_for('wl.employee@example.com')
        resp = self._call('POST', '/attendance/check-in', token=token, body={
            'latitude': FAR_LAT, 'longitude': FAR_LON, 'accuracy': 5.0, 'is_mocked': False,
        })
        self.assertEqual(resp.status_code, 403)
        body = resp.json()
        self.assertEqual(body['error']['code'], 'OUTSIDE_LOCATION')
        self.assertIn('distance', body['error']['details'])
        self.assertIn('radius', body['error']['details'])

    def test_checkin_none_restriction_far_away_ok(self):
        token = self._token_for('none.employee@example.com')
        resp = self._call('POST', '/attendance/check-in', token=token, body={
            'latitude': FAR_LAT, 'longitude': FAR_LON, 'accuracy': 5.0, 'is_mocked': False,
        })
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertIsNone(resp.json()['data']['location_name'])

    def test_checkin_company_mode_uses_company_coordinates(self):
        token = self._token_for('company.employee@example.com')
        resp = self._call('POST', '/attendance/check-in', token=token, body={
            'latitude': COMPANY_LAT, 'longitude': COMPANY_LON, 'accuracy': 5.0, 'is_mocked': False,
        })
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertAlmostEqual(resp.json()['data']['distance'], 0.0, delta=1.0)

    def test_checkin_location_not_configured(self):
        token = self._token_for('nolocation.employee@example.com')
        resp = self._call('POST', '/attendance/check-in', token=token, body={
            'latitude': COMPANY_LAT, 'longitude': COMPANY_LON, 'accuracy': 5.0, 'is_mocked': False,
        })
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()['error']['code'], 'LOCATION_NOT_CONFIGURED')

    def test_checkin_mock_location_blocked(self):
        token = self._token_for('none.employee@example.com')
        resp = self._call('POST', '/attendance/check-in', token=token, body={
            'latitude': COMPANY_LAT, 'longitude': COMPANY_LON, 'accuracy': 5.0, 'is_mocked': True,
        })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['error']['code'], 'MOCK_LOCATION')

    def test_checkin_location_required(self):
        token = self._token_for('none.employee@example.com')
        resp = self._call('POST', '/attendance/check-in', token=token, body={
            'is_mocked': False,
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error']['code'], 'LOCATION_REQUIRED')

    def test_already_checked_in(self):
        token = self._token_for('company.employee@example.com')
        body = {'latitude': COMPANY_LAT, 'longitude': COMPANY_LON, 'accuracy': 5.0, 'is_mocked': False}
        resp = self._call('POST', '/attendance/check-in', token=token, body=body)
        self.assertEqual(resp.status_code, 200, resp.text)
        resp = self._call('POST', '/attendance/check-in', token=token, body=body)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()['error']['code'], 'ALREADY_CHECKED_IN')

    def test_not_checked_in(self):
        token = self._token_for('none.employee@example.com')
        resp = self._call('POST', '/attendance/check-out', token=token, body={
            'latitude': COMPANY_LAT, 'longitude': COMPANY_LON, 'accuracy': 5.0, 'is_mocked': False,
        })
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()['error']['code'], 'NOT_CHECKED_IN')

    def test_stale_open_attendance_from_yesterday(self):
        yesterday = fields.Datetime.now() - timedelta(days=1, hours=1)
        self.env['hr.attendance'].sudo().create({
            'employee_id': self.emp_none.id,
            'check_in': yesterday,
        })
        token = self._token_for('none.employee@example.com')
        resp = self._call('GET', '/home', token=token)
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()['data']['attendance']['state'], 'checked_in')

        resp = self._call('POST', '/attendance/check-out', token=token, body={
            'latitude': COMPANY_LAT, 'longitude': COMPANY_LON, 'accuracy': 5.0, 'is_mocked': False,
        })
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()['data']['attendance']['state'], 'checked_out')

    def test_attendance_history_month(self):
        token = self._token_for('wl.employee@example.com')
        att = self.env['hr.attendance'].sudo().create({
            'employee_id': self.emp_wl.id,
            'check_in': '2026-08-10 05:00:00',
            'check_out': '2026-08-10 13:00:00',
        })
        resp = self._call('GET', '/attendance?month=2026-08', token=token)
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()['data']
        self.assertEqual(data['month'], '2026-08')
        self.assertGreaterEqual(data['summary']['present'], 1)
        dates = [d['date'] for d in data['days']]
        self.assertEqual(dates, sorted(dates, reverse=True))
        att.unlink()

    def test_attendance_history_bad_month(self):
        token = self._token_for('wl.employee@example.com')
        resp = self._call('GET', '/attendance?month=not-a-month', token=token)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error']['code'], 'VALIDATION_ERROR')

    def test_attendance_history_leave(self):
        if 'hr.leave' not in self.env:
            self.skipTest('hr_holidays is not installed in this test database.')

        leave_type = self.env['hr.leave.type'].sudo().create({
            'name': 'Mobile Test Leave Type',
            'company_id': self.company.id,
            'requires_allocation': 'no',
            'leave_validation_type': 'no_validation',
        })
        # 2026-08-17 is a Monday: a scheduled working day on emp_wl's
        # calendar (Mon-Fri 08:00-17:00), with no attendance recorded.
        leave = self.env['hr.leave'].sudo().create({
            'employee_id': self.emp_wl.id,
            'holiday_status_id': leave_type.id,
            'request_date_from': '2026-08-17',
            'request_date_to': '2026-08-17',
        })
        self.assertEqual(leave.state, 'validate')

        token = self._token_for('wl.employee@example.com')
        resp = self._call('GET', '/attendance?month=2026-08', token=token)
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()['data']
        self.assertGreaterEqual(data['summary']['leave'], 1)
        matching_days = [d for d in data['days'] if d['date'] == '2026-08-17']
        self.assertTrue(matching_days, "2026-08-17 should be in the days list")
        self.assertEqual(matching_days[0]['status'], 'leave')
        self.assertIsNone(matching_days[0]['check_in'])

    # ------------------------------------------------------------
    # home / profile
    # ------------------------------------------------------------
    def test_home(self):
        token = self._token_for('wl.employee@example.com')
        resp = self._call('GET', '/home', token=token)
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()['data']
        self.assertIn('server_time', data)
        self.assertEqual(data['restriction'], 'work_location')
        self.assertIsNotNone(data['geofence'])
        self.assertIsNone(data['geofence_error'])
        self.assertEqual(data['latest_payslip']['id'], self.payslip.id)

    def test_profile(self):
        token = self._token_for('wl.employee@example.com')
        resp = self._call('GET', '/profile', token=token)
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()['data']
        self.assertEqual(data['work_email'], 'wl.employee@example.com')
        self.assertEqual(data['code'], self.emp_wl.registration_number or self.emp_wl.barcode or str(self.emp_wl.id))

    # ------------------------------------------------------------
    # payslips
    # ------------------------------------------------------------
    def test_payslips_list(self):
        token = self._token_for('wl.employee@example.com')
        resp = self._call('GET', '/payslips?year=2026', token=token)
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()['data']
        self.assertIn(2026, data['years'])
        self.assertEqual(len(data['payslips']), 1)
        summary = data['payslips'][0]
        self.assertEqual(summary['id'], self.payslip.id)
        self.assertEqual(summary['state'], 'done')
        self.assertEqual(summary['net_wage'], 5200.0)
        self.assertEqual(summary['gross_wage'], 5500.0)

    def test_payslip_detail(self):
        token = self._token_for('wl.employee@example.com')
        resp = self._call('GET', '/payslips/%d' % self.payslip.id, token=token)
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()['data']
        self.assertEqual(data['worked_days'], 22.0)
        earning_codes = {e['code'] for e in data['earnings']}
        deduction_codes = {d['code'] for d in data['deductions']}
        self.assertEqual(earning_codes, {'BASIC', 'ALW1'})
        self.assertEqual(deduction_codes, {'DED1'})
        self.assertEqual(data['total_deductions'], 300.0)

    def test_payslip_pdf(self):
        # The controller's own route, over real HTTP: correct status/headers
        # and a non-empty body. Odoo intentionally renders qweb reports as
        # HTML instead of running wkhtmltopdf while --test-enable is active
        # (see ir.actions.report._pre_render_qweb_pdf) -- forcing real PDF
        # rendering from *inside* a live request handler would make
        # wkhtmltopdf fetch this same report's CSS/JS assets back over HTTP,
        # which deadlocks Odoo's single-threaded test server (it serializes
        # access to its test cursor). Production servers do not set
        # --test-enable, so this endpoint always returns real PDF bytes
        # there; that underlying rendering path is verified below without
        # going through HTTP.
        token = self._token_for('wl.employee@example.com')
        resp = self._call('GET', '/payslips/%d/pdf' % self.payslip.id, token=token)
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.headers.get('Content-Type'), 'application/pdf')
        self.assertTrue(resp.content)
        self.assertIn('attachment', resp.headers.get('Content-Disposition', ''))
        self.assertIn('Payslip-2026-08.pdf', resp.headers.get('Content-Disposition', ''))

        # Same rendering path the controller calls, exercised directly (as
        # odoo/addons/web/tests/test_reports.py does) so it actually proves
        # out real PDF bytes without the HTTP self-deadlock above.
        reports = self.payslip._get_pdf_reports()
        report = next(iter(reports.keys()))
        pdf_content, report_type = self.env['ir.actions.report'].sudo().with_context(
            force_report_rendering=True)._render_qweb_pdf(report, [self.payslip.id])
        self.assertEqual(report_type, 'pdf')
        self.assertTrue(pdf_content.startswith(b'%PDF'))

    def test_payslip_not_owned_returns_404(self):
        token = self._token_for('none.employee@example.com')
        resp = self._call('GET', '/payslips/%d' % self.payslip.id, token=token)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()['error']['code'], 'NOT_FOUND')
