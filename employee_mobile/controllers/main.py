# -*- coding: utf-8 -*-
import base64
import hashlib
import hmac
import logging
import re
import secrets
from datetime import date, datetime, time, timedelta

import pytz

from odoo import _, fields, http
from odoo.http import content_disposition, request
from odoo.tools.mimetypes import guess_mimetype

from ..exceptions import MobileApiError
from .utils import (
    get_json_body,
    haversine_distance,
    mobile_endpoint,
    success_envelope,
    to_employee_iso,
)

_logger = logging.getLogger(__name__)

MODULE_VERSION = '18.0.1.0.0'
PIN_RE = re.compile(r'^\d{4,8}$')


def _escape_ilike(value):
    return value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def _pin_matches(employee_pin, candidate_pin):
    """Constant-time PIN comparison that never raises.

    hmac.compare_digest() requires both str arguments to be ASCII-only (it
    raises TypeError otherwise, e.g. if the candidate PIN contains
    non-ASCII characters); comparing UTF-8 encoded bytes instead avoids
    that entirely.
    """
    if not employee_pin or not isinstance(candidate_pin, str):
        return False
    return hmac.compare_digest(employee_pin.encode('utf-8'), candidate_pin.encode('utf-8'))


def _lock_employee_row(env, employee_id):
    """Serialise concurrent check-in/check-out for the same employee."""
    env.cr.execute('SELECT id FROM hr_employee WHERE id = %s FOR NO KEY UPDATE', (employee_id,))


def _get_config_int(env, key, default):
    return int(env['ir.config_parameter'].sudo().get_param('employee_mobile.%s' % key, default))


# --------------------------------------------------------------------------
# Serialization helpers
# --------------------------------------------------------------------------

def _build_profile(employee):
    lang = employee.env.context.get('lang') or 'en_US'
    name = employee.name
    if lang.split('_')[0] == 'ar' and 'arabic_name' in employee._fields and employee.arabic_name:
        name = employee.arabic_name
    code = employee.registration_number or employee.barcode or str(employee.id)

    manager = None
    if employee.parent_id:
        manager = {
            'name': employee.parent_id.name,
            'email': employee.parent_id.work_email or None,
            'phone': employee.parent_id.work_phone or employee.parent_id.mobile_phone or None,
        }

    return {
        'id': employee.id,
        'name': name,
        'code': code,
        'job_title': employee.job_title or None,
        'department': employee.department_id.name or None,
        'company': employee.company_id.name or None,
        'work_email': employee.work_email or None,
        'mobile_phone': employee.mobile_phone or None,
        'work_location': employee.work_location_id.name or None,
        'manager': manager,
        'shift': _build_shift(employee),
        'attendance_restriction': employee.mobile_attendance_restriction,
        'image_version': _image_version(employee),
    }


def _image_version(employee):
    """Short fingerprint of the employee's photo, or ``None`` when they
    have none. Changes whenever HR uploads a new photo, so the app knows
    when to re-download ``/profile/image``."""
    if not employee.image_128:
        return None
    return hashlib.sha1(employee.image_128).hexdigest()[:12]


def _local_now(employee):
    tz = pytz.timezone(employee._get_tz() or 'UTC')
    return pytz.utc.localize(fields.Datetime.now()).astimezone(tz)


def _day_bounds_utc(local_date, tz):
    """Return (start, end) of ``local_date`` in ``tz``, converted to naive UTC
    datetimes (as stored on hr.attendance records)."""
    start_local = tz.localize(datetime.combine(local_date, time.min))
    end_local = start_local + timedelta(days=1)
    start_utc = start_local.astimezone(pytz.utc).replace(tzinfo=None)
    end_utc = end_local.astimezone(pytz.utc).replace(tzinfo=None)
    return start_utc, end_utc


def _day_schedule_start(employee, local_date, tz):
    """Return the local start time (tz-aware datetime) of the first scheduled
    interval for ``local_date``, ``'flexible'`` if the calendar has flexible
    hours, or ``None`` if there is no scheduled work that day."""
    calendar = employee.resource_calendar_id
    if not calendar:
        return None
    if getattr(calendar, 'flexible_hours', False):
        return 'flexible'
    start_local = tz.localize(datetime.combine(local_date, time.min))
    end_local = start_local + timedelta(days=1)
    resource = employee.resource_id
    intervals = calendar._attendance_intervals_batch(start_local, end_local, resource)[resource.id]
    if not intervals:
        return None
    return min(i[0] for i in intervals)


def _build_shift(employee):
    """Today's shift, or None on a day off / for a flexible calendar."""
    calendar = employee.resource_calendar_id
    if not calendar or getattr(calendar, 'flexible_hours', False):
        return None
    tz = pytz.timezone(employee._get_tz() or 'UTC')
    today = _local_now(employee).date()
    start_local = tz.localize(datetime.combine(today, time.min))
    end_local = start_local + timedelta(days=1)
    resource = employee.resource_id
    intervals = calendar._attendance_intervals_batch(start_local, end_local, resource)[resource.id]
    if not intervals:
        return None
    intervals = sorted(intervals, key=lambda i: i[0])
    start = intervals[0][0]
    end = intervals[-1][1]
    return {
        'name': calendar.name or _('Shift'),
        'start': start.strftime('%H:%M'),
        'end': end.strftime('%H:%M'),
    }


def _build_attendance_status(employee):
    Attendance = employee.env['hr.attendance'].sudo()
    open_att = Attendance.search(
        [('employee_id', '=', employee.id), ('check_out', '=', False)],
        order='check_in desc', limit=1)
    state = 'checked_in' if open_att else 'checked_out'
    check_in_iso = to_employee_iso(open_att.check_in, employee) if open_att else None

    tz = pytz.timezone(employee._get_tz() or 'UTC')
    today = _local_now(employee).date()
    day_start_utc, day_end_utc = _day_bounds_utc(today, tz)

    today_atts = Attendance.search([
        ('employee_id', '=', employee.id),
        ('check_in', '<', day_end_utc),
        '|', ('check_out', '>=', day_start_utc), ('check_out', '=', False),
    ], order='check_in asc')

    sessions = []
    today_worked_hours = 0.0
    now = fields.Datetime.now()
    for att in today_atts:
        if att.check_out:
            worked = att.worked_hours or 0.0
        else:
            start = max(att.check_in, day_start_utc)
            worked = max(0.0, (now - start).total_seconds() / 3600.0)
        today_worked_hours += worked
        sessions.append({
            'id': att.id,
            'check_in': to_employee_iso(att.check_in, employee),
            'check_out': to_employee_iso(att.check_out, employee) if att.check_out else None,
            'worked_hours': round(worked, 2),
            'location_name': att.mobile_check_in_location or None,
        })

    return {
        'state': state,
        'check_in': check_in_iso,
        'today_worked_hours': round(today_worked_hours, 2),
        'today_sessions': sessions,
    }, open_att


def _build_attendance_days(employee, year, month):
    env = employee.env
    tz = pytz.timezone(employee._get_tz() or 'UTC')
    month_start = date(year, month, 1)
    next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    today_local = _local_now(employee).date()
    list_end = min(next_month, today_local + timedelta(days=1))

    range_start_utc, _range_start_unused = _day_bounds_utc(month_start, tz)
    range_end_utc, _range_end_unused = _day_bounds_utc(next_month, tz)

    Attendance = env['hr.attendance'].sudo()
    attendances = Attendance.search([
        ('employee_id', '=', employee.id),
        ('check_in', '>=', range_start_utc),
        ('check_in', '<', range_end_utc),
    ], order='check_in asc')

    by_day = {}
    for att in attendances:
        local_day = pytz.utc.localize(att.check_in).astimezone(tz).date()
        by_day.setdefault(local_day, []).append(att)

    grace_minutes = employee.company_id.mobile_late_grace_minutes or 0

    leave_days = set()
    if 'hr.leave' in env:
        Leave = env['hr.leave'].sudo()
        margin_start, _margin_start_unused = _day_bounds_utc(month_start, tz)
        _margin_end_unused, margin_end = _day_bounds_utc(list_end - timedelta(days=1), tz)
        leaves = Leave.search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('date_from', '<', margin_end),
            ('date_to', '>=', margin_start),
        ])
        cur = month_start
        while cur < list_end:
            day_start_utc, day_end_utc = _day_bounds_utc(cur, tz)
            covered = leaves.filtered(
                lambda l: l.date_from < day_end_utc and l.date_to >= day_start_utc)
            if covered:
                leave_days.add(cur)
            cur += timedelta(days=1)

    days = []
    present = 0
    late = 0
    leave_count = 0

    all_days = set(by_day.keys()) | leave_days
    for local_day in all_days:
        atts = sorted(by_day.get(local_day, []), key=lambda a: a.check_in)
        if atts:
            first_in = atts[0]
            last_att = atts[-1]
            open_session = any(not a.check_out for a in atts)
            worked_hours = 0.0
            now = fields.Datetime.now()
            for a in atts:
                if a.check_out:
                    worked_hours += a.worked_hours or 0.0
                else:
                    worked_hours += max(0.0, (now - a.check_in).total_seconds() / 3600.0)

            if open_session:
                status = 'working'
            else:
                schedule_start = _day_schedule_start(employee, local_day, tz)
                if schedule_start in (None, 'flexible'):
                    status = 'on_time'
                else:
                    deadline = schedule_start + timedelta(minutes=grace_minutes)
                    first_in_local = pytz.utc.localize(first_in.check_in).astimezone(tz)
                    status = 'late' if first_in_local > deadline else 'on_time'

            if status == 'late':
                late += 1
            if status in ('working', 'on_time', 'late'):
                present += 1

            days.append({
                'date': local_day.strftime('%Y-%m-%d'),
                'check_in': to_employee_iso(first_in.check_in, employee),
                'check_out': to_employee_iso(last_att.check_out, employee) if not open_session else None,
                'worked_hours': round(worked_hours, 2),
                'status': status,
                'location_name': first_in.mobile_check_in_location or None,
                'sessions': [{
                    'id': a.id,
                    'check_in': to_employee_iso(a.check_in, employee),
                    'check_out': to_employee_iso(a.check_out, employee) if a.check_out else None,
                    'worked_hours': round(a.worked_hours or 0.0, 2),
                    'location_name': a.mobile_check_in_location or None,
                } for a in atts],
            })
        else:
            # Leave-only day.
            leave_count += 1
            days.append({
                'date': local_day.strftime('%Y-%m-%d'),
                'check_in': None,
                'check_out': None,
                'worked_hours': 0.0,
                'status': 'leave',
                'location_name': None,
                'sessions': [],
            })

    days.sort(key=lambda d: d['date'], reverse=True)
    summary = {'present': present, 'late': late, 'leave': leave_count}
    return summary, days


def _build_payslip_summary(payslip):
    return {
        'id': payslip.id,
        'name': payslip.name,
        'number': payslip.number or None,
        'date_from': fields.Date.to_string(payslip.date_from),
        'date_to': fields.Date.to_string(payslip.date_to),
        'state': payslip.state,
        'paid_date': fields.Date.to_string(payslip.paid_date) if payslip.paid_date else None,
        'net_wage': payslip.net_wage,
        'gross_wage': payslip.gross_wage,
        'currency': payslip.currency_id.name or None,
    }


def _build_payslip_detail(payslip):
    summary = _build_payslip_summary(payslip)
    lines = payslip.line_ids.filtered(
        lambda l: l.appears_on_payslip and l.category_id.code not in ('GROSS', 'NET'))
    earnings = []
    deductions = []
    total_deductions = 0.0
    for line in lines:
        entry = {'name': line.name, 'code': line.code, 'amount': line.total}
        if line.total < 0:
            deductions.append(entry)
            total_deductions += abs(line.total)
        else:
            earnings.append(entry)

    worked_days = sum(
        wd.number_of_days for wd in payslip.worked_days_line_ids if wd.code == 'WORK100')

    summary.update({
        'worked_days': worked_days,
        'earnings': earnings,
        'deductions': deductions,
        'total_deductions': total_deductions,
    })
    return summary


def _register_login_failures(env, candidates):
    """Increment the failed-attempt counter for every employee in
    ``candidates`` (normally just one; more than one only happens when
    several employees share a work_email, e.g. across companies), commit
    immediately so the counters survive the rollback the error handler is
    about to do, then always raise: ``ACCOUNT_LOCKED`` when there was
    exactly one candidate and this attempt just locked it, otherwise
    ``INVALID_CREDENTIALS`` (a lock on just one of several same-email
    candidates is not surfaced, so the response never hints at which one
    it was).
    """
    max_attempts = _get_config_int(env, 'max_failed_attempts', 5)
    lockout_minutes = _get_config_int(env, 'lockout_minutes', 15)
    now = fields.Datetime.now()

    just_locked_single = False
    retry_after = None
    for employee in candidates:
        attempts = (employee.mobile_failed_attempts or 0) + 1
        vals = {'mobile_failed_attempts': attempts}
        locked = attempts >= max_attempts
        if locked:
            vals['mobile_locked_until'] = now + timedelta(minutes=lockout_minutes)
            if len(candidates) == 1:
                just_locked_single = True
                retry_after = lockout_minutes * 60
        employee.sudo().write(vals)

    env.cr.commit()

    if just_locked_single:
        raise MobileApiError(
            'ACCOUNT_LOCKED', 429,
            _("Too many failed attempts. Please try again later."),
            {'retry_after_seconds': retry_after})
    raise MobileApiError('INVALID_CREDENTIALS', 401, _("Incorrect email or PIN."))


class MobileApiController(http.Controller):

    # ----------------------------------------------------------------
    # Health check
    # ----------------------------------------------------------------
    @http.route('/api/mobile/ping', type='http', auth='public', methods=['GET'],
                csrf=False, readonly=True)
    @mobile_endpoint(auth_required=False)
    def mobile_ping(self, **kwargs):
        return request.make_json_response(
            success_envelope({'ok': True, 'version': MODULE_VERSION}))

    # ----------------------------------------------------------------
    # Auth
    # ----------------------------------------------------------------
    @http.route('/api/mobile/login', type='http', auth='public', methods=['POST'],
                csrf=False, readonly=False)
    @mobile_endpoint(auth_required=False)
    def mobile_login(self, **kwargs):
        env = request.env
        body = get_json_body()
        email = (body.get('email') or '').strip()
        pin = body.get('pin')
        device = body.get('device') or {}
        if not isinstance(device, dict):
            device = {}

        if not email or not pin or not isinstance(pin, str):
            raise MobileApiError('VALIDATION_ERROR', 400, _("Work email and PIN are required."))

        # Only active employees with mobile app access enabled are eligible. An
        # unknown email, a disabled account and a wrong PIN must all be
        # indistinguishable from the outside, so they all fall through to the
        # same INVALID_CREDENTIALS below.
        Employee = env['hr.employee'].sudo()
        candidates = Employee.search([
            ('work_email', '=ilike', _escape_ilike(email)),
            ('mobile_app_access', '=', True),
        ])

        if not candidates:
            # Unknown email: nothing to register a failure against.
            raise MobileApiError('INVALID_CREDENTIALS', 401, _("Incorrect email or PIN."))

        # work_email is not guaranteed unique across companies, so more than
        # one employee can share it: match by PIN among all of them.
        matched = candidates.filtered(lambda e: _pin_matches(e.pin, pin))

        if len(matched) > 1:
            _logger.warning(
                "Mobile login: %d employees share work email %r with the same PIN; "
                "fix the duplicate work_email/PIN combination in HR.",
                len(matched), email)
            raise MobileApiError('INVALID_CREDENTIALS', 401, _("Incorrect email or PIN."))

        if len(matched) != 1:
            _register_login_failures(env, candidates)  # always raises

        employee = matched
        now = fields.Datetime.now()

        if employee.mobile_locked_until and employee.mobile_locked_until > now:
            retry_after = max(1, int((employee.mobile_locked_until - now).total_seconds()))
            raise MobileApiError(
                'ACCOUNT_LOCKED', 429,
                _("Too many failed attempts. Please try again later."),
                {'retry_after_seconds': retry_after})

        if employee.mobile_failed_attempts or employee.mobile_locked_until:
            employee.write({'mobile_failed_attempts': 0, 'mobile_locked_until': False})

        token_str = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token_str.encode('utf-8')).hexdigest()
        validity_days = _get_config_int(env, 'token_validity_days', 30)
        expires_at = now + timedelta(days=validity_days)

        env['hr.employee.mobile.token'].sudo().create({
            'employee_id': employee.id,
            'token_hash': token_hash,
            'device_id': device.get('id'),
            'device_name': device.get('name'),
            'platform': device.get('platform'),
            'app_version': device.get('app_version'),
            'last_used': now,
            'expires_at': expires_at,
        })

        employee = employee.with_company(employee.company_id)
        data = {
            'token': token_str,
            'expires_at': to_employee_iso(expires_at, employee),
            'employee': _build_profile(employee),
        }
        return request.make_json_response(success_envelope(data))

    @http.route('/api/mobile/logout', type='http', auth='public', methods=['POST'],
                csrf=False, readonly=False)
    @mobile_endpoint(auth_required=True)
    def mobile_logout(self, employee=None, token=None, **kwargs):
        token.sudo().write({'active': False})
        return request.make_json_response(success_envelope({}))

    @http.route('/api/mobile/profile', type='http', auth='public', methods=['GET'],
                csrf=False, readonly=False)
    @mobile_endpoint(auth_required=True)
    def mobile_profile(self, employee=None, token=None, **kwargs):
        return request.make_json_response(success_envelope(_build_profile(employee)))

    @http.route('/api/mobile/profile/image', type='http', auth='public', methods=['GET'],
                csrf=False, readonly=True)
    @mobile_endpoint(auth_required=True)
    def mobile_profile_image(self, employee=None, token=None, **kwargs):
        image = employee.image_256
        if not image:
            raise MobileApiError('NOT_FOUND', 404, _("No photo on file."))
        content = base64.b64decode(image)
        headers = [
            ('Content-Type', guess_mimetype(content, default='image/png')),
            ('Content-Length', len(content)),
            ('Cache-Control', 'private, no-cache'),
        ]
        return request.make_response(content, headers=headers)

    @http.route('/api/mobile/change-pin', type='http', auth='public', methods=['POST'],
                csrf=False, readonly=False)
    @mobile_endpoint(auth_required=True)
    def mobile_change_pin(self, employee=None, token=None, **kwargs):
        body = get_json_body()
        current_pin = body.get('current_pin')
        new_pin = body.get('new_pin')

        if not isinstance(current_pin, str) or not isinstance(new_pin, str):
            raise MobileApiError('VALIDATION_ERROR', 400, _("Current and new PIN are required."))

        current_ok = _pin_matches(employee.pin, current_pin)
        if not current_ok:
            raise MobileApiError('PIN_INCORRECT', 400, _("Your current PIN is incorrect."))

        if not PIN_RE.match(new_pin) or new_pin == current_pin:
            raise MobileApiError(
                'PIN_FORMAT', 400,
                _("The new PIN must be 4 to 8 digits and different from the current one."))

        employee.with_context(mobile_keep_token_ids=[token.id]).write({'pin': new_pin})
        return request.make_json_response(success_envelope({}))

    # ----------------------------------------------------------------
    # Home
    # ----------------------------------------------------------------
    @http.route('/api/mobile/home', type='http', auth='public', methods=['GET'],
                csrf=False, readonly=False)
    @mobile_endpoint(auth_required=True)
    def mobile_home(self, employee=None, token=None, **kwargs):
        env = request.env
        now = fields.Datetime.now()
        attendance_status, _open_att = _build_attendance_status(employee)

        geofence = None
        geofence_error = None
        try:
            geofence = employee._mobile_get_geofence()
        except MobileApiError as exc:
            if exc.code != 'LOCATION_NOT_CONFIGURED':
                raise
            geofence_error = exc.code

        today_local = _local_now(employee).date()
        summary, _days = _build_attendance_days(employee, today_local.year, today_local.month)

        Payslip = env['hr.payslip'].sudo()
        latest_payslip = Payslip.search([
            ('employee_id', '=', employee.id),
            ('state', 'in', ('done', 'paid')),
        ], order='date_from desc', limit=1)

        data = {
            'server_time': to_employee_iso(now, employee),
            'attendance': attendance_status,
            'restriction': employee.mobile_attendance_restriction,
            'geofence': geofence,
            'geofence_error': geofence_error,
            'shift': _build_shift(employee),
            'month_present_days': summary['present'],
            'latest_payslip': {
                'id': latest_payslip.id,
                'date_from': fields.Date.to_string(latest_payslip.date_from),
            } if latest_payslip else None,
        }
        return request.make_json_response(success_envelope(data))

    # ----------------------------------------------------------------
    # Attendance
    # ----------------------------------------------------------------
    def _read_location_payload(self):
        body = get_json_body()
        latitude = body.get('latitude')
        longitude = body.get('longitude')
        if latitude is None or longitude is None:
            raise MobileApiError('LOCATION_REQUIRED', 400, _("Your location is required."))
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            raise MobileApiError('LOCATION_REQUIRED', 400, _("Your location is required."))
        accuracy = body.get('accuracy')
        try:
            accuracy = float(accuracy) if accuracy is not None else None
        except (TypeError, ValueError):
            accuracy = None
        is_mocked = bool(body.get('is_mocked'))
        return latitude, longitude, accuracy, is_mocked

    def _check_mock_location(self, employee, is_mocked):
        if is_mocked and employee.company_id.mobile_block_mock_location:
            raise MobileApiError(
                'MOCK_LOCATION', 403,
                _("Mock/fake GPS locations are not allowed. Disable mock location and try again."))

    def _resolve_geofence_distance(self, employee, latitude, longitude):
        """Return (geofence_or_None, distance_or_None, location_name_or_None).
        Raises OUTSIDE_LOCATION if the point is outside the geofence."""
        geofence = employee._mobile_get_geofence()
        if not geofence:
            return None, None, None
        distance = haversine_distance(latitude, longitude, geofence['latitude'], geofence['longitude'])
        if distance > geofence['radius']:
            raise MobileApiError(
                'OUTSIDE_LOCATION', 403,
                _("You are outside the allowed location."),
                {
                    'distance': round(distance, 1),
                    'radius': geofence['radius'],
                    'location_name': geofence['name'],
                })
        return geofence, round(distance, 1), geofence['name']

    @http.route('/api/mobile/attendance/check-in', type='http', auth='public',
                methods=['POST'], csrf=False, readonly=False)
    @mobile_endpoint(auth_required=True)
    def mobile_check_in(self, employee=None, token=None, **kwargs):
        env = request.env
        latitude, longitude, accuracy, is_mocked = self._read_location_payload()
        self._check_mock_location(employee, is_mocked)

        _lock_employee_row(env, employee.id)

        Attendance = env['hr.attendance'].sudo()
        open_att = Attendance.search(
            [('employee_id', '=', employee.id), ('check_out', '=', False)], limit=1)
        if open_att:
            raise MobileApiError(
                'ALREADY_CHECKED_IN', 409, _("You are already checked in."))

        _geofence, distance, location_name = self._resolve_geofence_distance(
            employee, latitude, longitude)

        in_browser = "Mobile App %s %s" % (token.platform or '', token.app_version or '')
        Attendance.create({
            'employee_id': employee.id,
            'check_in': fields.Datetime.now(),
            'in_latitude': latitude,
            'in_longitude': longitude,
            'in_ip_address': request.httprequest.remote_addr,
            'in_browser': in_browser.strip(),
            'in_mode': 'mobile',
            'check_in_latitude': latitude,
            'check_in_longitude': longitude,
            'mobile_check_in_location': location_name,
            'mobile_check_in_distance': distance or 0.0,
        })

        attendance_status, _open = _build_attendance_status(employee)
        data = {
            'attendance': attendance_status,
            'distance': distance,
            'location_name': location_name,
        }
        return request.make_json_response(success_envelope(data))

    @http.route('/api/mobile/attendance/check-out', type='http', auth='public',
                methods=['POST'], csrf=False, readonly=False)
    @mobile_endpoint(auth_required=True)
    def mobile_check_out(self, employee=None, token=None, **kwargs):
        env = request.env
        latitude, longitude, accuracy, is_mocked = self._read_location_payload()
        self._check_mock_location(employee, is_mocked)

        _lock_employee_row(env, employee.id)

        Attendance = env['hr.attendance'].sudo()
        open_att = Attendance.search(
            [('employee_id', '=', employee.id), ('check_out', '=', False)],
            order='check_in desc', limit=1)
        if not open_att:
            raise MobileApiError('NOT_CHECKED_IN', 409, _("You are not checked in."))

        _geofence, distance, location_name = self._resolve_geofence_distance(
            employee, latitude, longitude)

        out_browser = "Mobile App %s %s" % (token.platform or '', token.app_version or '')
        open_att.write({
            'check_out': fields.Datetime.now(),
            'out_latitude': latitude,
            'out_longitude': longitude,
            'out_ip_address': request.httprequest.remote_addr,
            'out_browser': out_browser.strip(),
            'out_mode': 'mobile',
            'check_out_latitude': latitude,
            'check_out_longitude': longitude,
            'mobile_check_out_location': location_name,
            'mobile_check_out_distance': distance or 0.0,
        })

        attendance_status, _open = _build_attendance_status(employee)
        data = {
            'attendance': attendance_status,
            'distance': distance,
            'location_name': location_name,
        }
        return request.make_json_response(success_envelope(data))

    @http.route('/api/mobile/attendance', type='http', auth='public', methods=['GET'],
                csrf=False, readonly=False)
    @mobile_endpoint(auth_required=True)
    def mobile_attendance_history(self, employee=None, token=None, **kwargs):
        month_param = request.httprequest.args.get('month')
        today_local = _local_now(employee).date()
        if month_param:
            try:
                year, month = (int(p) for p in month_param.split('-'))
                date(year, month, 1)
            except (ValueError, TypeError):
                raise MobileApiError(
                    'VALIDATION_ERROR', 400, _("The month must be in YYYY-MM format."))
        else:
            year, month = today_local.year, today_local.month

        summary, days = _build_attendance_days(employee, year, month)
        data = {
            'month': '%04d-%02d' % (year, month),
            'summary': summary,
            'days': days,
        }
        return request.make_json_response(success_envelope(data))

    # ----------------------------------------------------------------
    # Payslips
    # ----------------------------------------------------------------
    @http.route('/api/mobile/payslips', type='http', auth='public', methods=['GET'],
                csrf=False, readonly=False)
    @mobile_endpoint(auth_required=True)
    def mobile_payslips(self, employee=None, token=None, **kwargs):
        env = request.env
        Payslip = env['hr.payslip'].sudo()
        all_slips = Payslip.search([
            ('employee_id', '=', employee.id),
            ('state', 'in', ('done', 'paid')),
        ], order='date_from desc')

        years = sorted({slip.date_from.year for slip in all_slips if slip.date_from}, reverse=True)

        year_param = request.httprequest.args.get('year')
        if year_param:
            try:
                year = int(year_param)
            except ValueError:
                raise MobileApiError('VALIDATION_ERROR', 400, _("Invalid year."))
        else:
            year = years[0] if years else fields.Date.today().year

        slips_for_year = all_slips.filtered(lambda s: s.date_from and s.date_from.year == year)
        data = {
            'years': years,
            'payslips': [_build_payslip_summary(slip) for slip in slips_for_year],
        }
        return request.make_json_response(success_envelope(data))

    @http.route('/api/mobile/payslips/<int:payslip_id>', type='http', auth='public',
                methods=['GET'], csrf=False, readonly=False)
    @mobile_endpoint(auth_required=True)
    def mobile_payslip_detail(self, payslip_id, employee=None, token=None, **kwargs):
        payslip = self._get_own_payslip(employee, payslip_id)
        return request.make_json_response(success_envelope(_build_payslip_detail(payslip)))

    @http.route('/api/mobile/payslips/<int:payslip_id>/pdf', type='http', auth='public',
                methods=['GET'], csrf=False, readonly=False)
    @mobile_endpoint(auth_required=True)
    def mobile_payslip_pdf(self, payslip_id, employee=None, token=None, **kwargs):
        payslip = self._get_own_payslip(employee, payslip_id)
        env = request.env
        reports = payslip._get_pdf_reports()
        report = next(iter(reports.keys()))
        # Odoo renders qweb reports as HTML instead of spawning wkhtmltopdf
        # while odoo-bin runs with --test-enable/--test-tags (see
        # ir.actions.report._pre_render_qweb_pdf). That only affects our own
        # automated test suite; a normal (non-test) server always gets real
        # PDF bytes here. We deliberately do NOT force
        # `force_report_rendering=True` in production code: doing so from
        # inside a live request handler makes wkhtmltopdf fetch this same
        # report's CSS/JS assets back over HTTP, which is fine in
        # production (multiple workers/threads) but deadlocks Odoo's
        # single test server, which serializes access to its test cursor.
        pdf_content, _report_type = env['ir.actions.report'].sudo()._render_qweb_pdf(
            report, [payslip.id])
        filename = 'Payslip-%04d-%02d.pdf' % (payslip.date_from.year, payslip.date_from.month)
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition', content_disposition(filename)),
        ]
        return request.make_response(pdf_content, headers=headers)

    def _get_own_payslip(self, employee, payslip_id):
        Payslip = request.env['hr.payslip'].sudo()
        payslip = Payslip.search([
            ('id', '=', payslip_id),
            ('employee_id', '=', employee.id),
            ('state', 'in', ('done', 'paid')),
        ], limit=1)
        if not payslip:
            raise MobileApiError('NOT_FOUND', 404, _("Payslip not found."))
        return payslip
