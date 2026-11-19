import base64
import io
from collections import defaultdict
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
import xlsxwriter
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError


class AttendanceAnalysisDashboard(models.AbstractModel):
    _name = 'attendance.analysis.dashboard'
    _description = 'Attendance Analysis Dashboard'

    @api.model
    def _check_access(self):
        if not self.env.user.has_group('hr_customs.group_attendance_dashboard'):
            raise AccessError(_('You do not have access to the Attendance Dashboard.'))

    @api.model
    def _get_dates(self, filters):
        today = fields.Date.context_today(self)
        preset = filters.get('date_preset', 'current_month')
        start = today.replace(day=1)
        end = start + relativedelta(months=1, days=-1)
        if preset == 'today':
            start = end = today
        elif preset == 'yesterday':
            start = end = today - timedelta(days=1)
        elif preset == 'this_week':
            start = today - timedelta(days=(today.weekday() + 2) % 7)
            end = start + timedelta(days=6)
        elif preset == 'last_week':
            start = today - timedelta(days=(today.weekday() + 2) % 7 + 7)
            end = start + timedelta(days=6)
        elif preset == 'custom':
            start = fields.Date.to_date(filters.get('date_from') or today)
            end = fields.Date.to_date(filters.get('date_to') or today)
        elif preset == 'none':
            return False, today
        if start > end:
            raise UserError(_('The start date cannot be later than the end date.'))
        return start, min(end, today)

    @api.model
    def get_filter_options(self):
        self._check_access()
        employees = self.env['hr.employee'].search([])
        employees = employees.sorted(key=lambda e: (not bool(e.registration_number2), (e.registration_number2 or '').casefold(), e.name.casefold(), e.id))
        departments = self.env['hr.department'].search([], order='name')
        return {'employees': [{'id': e.id, 'name': e.name, 'code': e.registration_number2 or ''} for e in employees], 'departments': [{'id': d.id, 'name': d.complete_name or d.name} for d in departments]}

    @api.model
    def _get_special_calendars(self, start, end):
        return self.env['resource.calendar']._get_special_calendars(start, end)

    @api.model
    def _get_applicable_calendar(self, employee, day, regular_calendar, special_calendars):
        return employee._get_special_calendar(day, regular_calendar, special_calendars)

    @api.model
    def _get_report(self, filters):
        self._check_access()
        filters = filters or {}
        start, end = self._get_dates(filters)
        source = filters.get('source', 'attendance')
        status_filter = filters.get('status', 'all')
        employee_ids = [int(x) for x in filters.get('employee_ids', [])]
        department_ids = [int(x) for x in filters.get('department_ids', [])]
        domain = []
        if employee_ids:
            domain.append(('id', 'in', employee_ids))
        if department_ids:
            domain.append(('department_id', 'in', department_ids))
        employees = self.env['hr.employee'].search(domain)
        keys = ('employees', 'present', 'absent', 'late', 'early', 'leave', 'weekend', 'holiday', 'missing_in', 'missing_out', 'worked_hours', 'overtime_hours', 'scheduled_hours', 'days', 'no_contract')
        summary = {key: 0 for key in keys}
        summary.update({'attendance_rate': 0, 'absence_rate': 0, 'hours_difference': 0})
        def empty_report():
            return {'rows': [], 'summary': summary, 'date_from': str(start or end), 'date_to': str(end), 'total': 0}
        if start and start > end:
            return empty_report()
        contract_domain = [('employee_id', 'in', employees.ids), ('state', 'in', ['open', 'close'])]
        if source in ('attendance', 'calendar'):
            contract_domain.append(('work_entry_source', '=', source))
        if start:
            contract_domain += [('date_start', '<=', end), '|', ('date_end', '=', False), ('date_end', '>=', start)]
        else:
            contract_domain.append(('date_start', '<=', end))
        contracts = self.env['hr.contract'].search(contract_domain, order='date_start desc, id desc')
        by_employee = defaultdict(list)
        for contract in contracts:
            by_employee[contract.employee_id.id].append(contract)
        employees = employees.filtered(lambda e: e.id in by_employee)
        employees = employees.sorted(key=lambda e: (not bool(e.registration_number2), (e.registration_number2 or '').casefold(), e.name.casefold(), e.id))
        summary['employees'] = len(employees)
        today = fields.Date.context_today(self)
        if not start:
            start = min(contracts.mapped('date_start')) if contracts else today
        if not employees:
            return empty_report()
        special_calendars = self._get_special_calendars(start, end)
        tz_map = {}
        for employee in employees:
            calendar = by_employee[employee.id][0].resource_calendar_id or employee.resource_calendar_id
            tz_name = (calendar.tz if calendar else False) or self.env.user.tz or 'UTC'
            try:
                tz_map[employee.id] = ZoneInfo(tz_name)
            except (KeyError, ValueError):
                tz_map[employee.id] = ZoneInfo('UTC')
        utc_start = datetime.combine(start - timedelta(days=2), time.min)
        utc_end = datetime.combine(end + timedelta(days=3), time.min)
        attendances = self.env['hr.attendance'].search([('employee_id', 'in', employees.ids), ('check_in', '>=', fields.Datetime.to_string(utc_start)), ('check_in', '<', fields.Datetime.to_string(utc_end))], order='check_in')
        attendance_map = defaultdict(list)
        for attendance in attendances:
            day = fields.Datetime.to_datetime(attendance.check_in).replace(tzinfo=timezone.utc).astimezone(tz_map[attendance.employee_id.id]).date()
            if start <= day <= end:
                attendance_map[(attendance.employee_id.id, day)].append(attendance)
        leaves = self.env['hr.leave'].search([('employee_id', 'in', employees.ids), ('state', '=', 'validate'), ('request_date_from', '<=', end), ('request_date_to', '>=', start)])
        leave_map = {}
        for leave in leaves:
            day = max(start, leave.request_date_from)
            until = min(end, leave.request_date_to)
            while day <= until:
                leave_map[(leave.employee_id.id, day)] = leave.holiday_status_id.name
                day += timedelta(days=1)
        calendar_ids = list(set(contracts.mapped('resource_calendar_id').ids + special_calendars.ids))
        holidays = self.env['resource.calendar.leaves'].search([('resource_id', '=', False), ('date_from', '<', fields.Datetime.to_string(utc_end)), ('date_to', '>', fields.Datetime.to_string(utc_start)), '|', ('calendar_id', '=', False), ('calendar_id', 'in', calendar_ids)])
        holiday_map = defaultdict(list)
        for holiday in holidays:
            for employee in employees:
                tz = tz_map[employee.id]
                first = fields.Datetime.to_datetime(holiday.date_from).replace(tzinfo=timezone.utc).astimezone(tz).date()
                last = (fields.Datetime.to_datetime(holiday.date_to) - timedelta(microseconds=1)).replace(tzinfo=timezone.utc).astimezone(tz).date()
                day = max(start, first)
                while day <= min(end, last):
                    contract = next((c for c in by_employee[employee.id] if c.date_start <= day and (not c.date_end or c.date_end >= day)), False)
                    if contract:
                        regular = contract.resource_calendar_id or employee.resource_calendar_id
                        selected = self._get_applicable_calendar(employee, day, regular, special_calendars)
                        if not holiday.calendar_id or holiday.calendar_id == selected:
                            holiday_map[(employee.id, day)].append(holiday.name or 'Public Holiday')
                    day += timedelta(days=1)
        line_fields = self.env['resource.calendar.attendance']._fields
        rows = []
        now_utc = datetime.now(timezone.utc)
        for employee in employees:
            tz = tz_map[employee.id]
            company = employee.company_id
            company_grace = max(0.0, float(company.overtime_company_threshold or 0)) if 'overtime_company_threshold' in company._fields else 0.0
            employee_grace = max(0.0, float(company.overtime_employee_threshold or 0)) if 'overtime_employee_threshold' in company._fields else 0.0
            day = start
            while day <= end:
                contract = next((c for c in by_employee[employee.id] if c.date_start <= day and (not c.date_end or c.date_end >= day)), False)
                regular = (contract.resource_calendar_id or employee.resource_calendar_id) if contract else False
                calendar = self._get_applicable_calendar(employee, day, regular, special_calendars) if contract else False
                lines = self.env['resource.calendar.attendance']
                shift = calendar.name if calendar else ''
                shift_time = ''
                scheduled_start = scheduled_end = False
                scheduled_hours = 0.0
                if calendar:
                    lines = calendar.attendance_ids.filtered(lambda a: int(a.dayofweek) == day.weekday())
                    if 'date_from' in line_fields:
                        lines = lines.filtered(lambda a: not a.date_from or a.date_from <= day)
                    if 'date_to' in line_fields:
                        lines = lines.filtered(lambda a: not a.date_to or a.date_to >= day)
                    if calendar.two_weeks_calendar:
                        lines = lines.filtered(lambda a: not a.week_type or int(a.week_type) == day.isocalendar().week % 2)
                    lines = lines.sorted(key=lambda a: a.hour_from)
                    if lines:
                        first, last = lines[0], lines[-1]
                        from_hour, to_hour = float(first.hour_from), float(last.hour_to)
                        if to_hour <= from_hour:
                            to_hour += 24
                        scheduled_start = datetime.combine(day, time.min, tzinfo=tz) + timedelta(hours=from_hour)
                        scheduled_end = datetime.combine(day, time.min, tzinfo=tz) + timedelta(hours=to_hour)
                        scheduled_hours = sum(max(0.0, float(line.hour_to) - float(line.hour_from)) for line in lines)
                        shift_time = '%s - %s' % (scheduled_start.strftime('%H:%M'), scheduled_end.strftime('%H:%M'))
                punches = attendance_map.get((employee.id, day), [])
                check_ins = [fields.Datetime.to_datetime(a.check_in).replace(tzinfo=timezone.utc).astimezone(tz) for a in punches]
                check_outs = [fields.Datetime.to_datetime(a.check_out).replace(tzinfo=timezone.utc).astimezone(tz) for a in punches if a.check_out]
                first_in, last_out = (min(check_ins) if check_ins else False), (max(check_outs) if check_outs else False)
                worked = sum(a.worked_hours or 0.0 for a in punches)
                late_raw = max(0.0, (first_in - scheduled_start).total_seconds() / 60.0) if first_in and scheduled_start else 0.0
                early_raw = max(0.0, (scheduled_end - last_out).total_seconds() / 60.0) if last_out and scheduled_end else 0.0
                late = int(late_raw + 0.999999) if late_raw > employee_grace else 0
                early = int(early_raw + 0.999999) if early_raw > employee_grace else 0
                missing_out = bool(punches and any(not a.check_out for a in punches) and day < today)
                holiday_names, leave_name = holiday_map.get((employee.id, day), []), leave_map.get((employee.id, day))
                if not contract:
                    status = 'No Contract'
                elif first_in:
                    status = 'Missing Check-Out' if missing_out else 'Present'
                    if not missing_out and late and early:
                        status = 'Late In / Early Out'
                    elif not missing_out and late:
                        status = 'Late In'
                    elif not missing_out and early:
                        status = 'Early Out'
                elif holiday_names:
                    status = 'Public Holiday'
                elif leave_name:
                    status = 'Leave'
                elif not lines:
                    status = 'Weekend'
                else:
                    status = 'Absent'
                if contract and first_in and not last_out and (not scheduled_end or scheduled_end > now_utc.astimezone(tz)):
                    status = 'In Progress'
                remarks = ', '.join(holiday_names) if holiday_names else leave_name or ''
                if not contract:
                    remarks = 'No matching contract on this date'
                if not contract or (not first_in and status in ('Weekend', 'Leave', 'Public Holiday')):
                    scheduled_hours = 0.0
                # Use the actual special/regular schedule, not an older stored overtime value based on another shift.
                overtime_raw = max(0.0, (worked - scheduled_hours) * 60.0) if contract and first_in and last_out and lines else 0.0
                overtime = overtime_raw / 60.0 if overtime_raw > company_grace else 0.0
                if not lines and first_in and last_out and contract:
                    overtime = worked if worked * 60.0 > company_grace else 0.0
                row = {
                    'date': str(day), 'day': day.strftime('%A'), 'code': employee.registration_number2 or '',
                    'employee': employee.name, 'employee_id': employee.id, 'department': employee.department_id.name or '',
                    'department_id': employee.department_id.id or 0, 'shift': shift, 'shift_time': shift_time,
                    'check_in': first_in.strftime('%H:%M') if first_in else '', 'check_out': last_out.strftime('%H:%M') if last_out else '',
                    'late': late, 'early': early, 'worked': round(worked, 2), 'overtime': round(max(0.0, overtime), 2),
                    'scheduled_hours': round(scheduled_hours, 2), 'status': status, 'remarks': remarks,
                }
                summary['days'] += 1
                if contract:
                    if first_in:
                        summary['present'] += 1
                        summary['worked_hours'] += worked
                        summary['overtime_hours'] += overtime
                    summary['scheduled_hours'] += scheduled_hours
                    if late:
                        summary['late'] += 1
                    if early:
                        summary['early'] += 1
                    if status == 'Absent':
                        summary['absent'] += 1
                        summary['missing_in'] += 1
                    if status == 'Missing Check-Out':
                        summary['missing_out'] += 1
                    if status == 'Leave':
                        summary['leave'] += 1
                    if status == 'Weekend':
                        summary['weekend'] += 1
                    if status == 'Public Holiday':
                        summary['holiday'] += 1
                else:
                    summary['no_contract'] += 1
                matches = (
                    status_filter == 'all' or status_filter == 'late' and late > 0 and bool(contract)
                    or status_filter == 'early' and early > 0 and bool(contract)
                    or status_filter == 'late_early' and (late > 0 or early > 0) and bool(contract)
                    or status_filter == 'missing_in' and status == 'Absent'
                    or status_filter == 'missing_out' and status == 'Missing Check-Out'
                    or status_filter == 'absent' and status == 'Absent'
                    or status_filter == 'leave' and status == 'Leave'
                    or status_filter == 'weekend' and status == 'Weekend'
                    or status_filter == 'holiday' and status == 'Public Holiday'
                    or status_filter == 'present' and bool(first_in) and bool(contract)
                    or status_filter == 'no_contract' and status == 'No Contract'
                )
                if matches:
                    rows.append(row)
                day += timedelta(days=1)
        for key in ('worked_hours', 'overtime_hours', 'scheduled_hours'):
            summary[key] = round(summary[key], 2)
        summary['hours_difference'] = round(summary['worked_hours'] - summary['scheduled_hours'], 2)
        scheduled_days = summary['present'] + summary['absent']
        summary['attendance_rate'] = round(summary['present'] * 100 / scheduled_days, 1) if scheduled_days else 0
        summary['absence_rate'] = round(summary['absent'] * 100 / scheduled_days, 1) if scheduled_days else 0
        return {'rows': rows, 'summary': summary, 'date_from': str(start), 'date_to': str(end), 'total': len(rows)}

    @api.model
    def _get_analytics(self, rows, date_from, date_to):
        employees, departments = {}, {}
        for row in rows:
            employee_id, department_id = row['employee_id'], row['department_id']
            present = int(bool(row['check_in']) and row['status'] != 'No Contract')
            absent = int(row['status'] == 'Absent')
            late = int(row['late'] > 0 and row['status'] != 'No Contract')
            early = int(row['early'] > 0 and row['status'] != 'No Contract')
            if employee_id not in employees:
                employees[employee_id] = {'id': employee_id, 'code': row['code'], 'employee': row['employee'], 'department': row['department'] or 'No Department', 'department_id': department_id, 'present': 0, 'absent': 0, 'late': 0, 'early': 0, 'late_minutes': 0, 'early_minutes': 0, 'leave': 0, 'missing_out': 0, 'worked': 0.0, 'overtime': 0.0, 'scheduled': 0.0}
            if department_id not in departments:
                departments[department_id] = {'id': department_id, 'name': row['department'] or 'No Department', 'present': 0, 'absent': 0, 'late': 0, 'early': 0, 'employees': set()}
            employee, department = employees[employee_id], departments[department_id]
            for key, amount in [('present', present), ('absent', absent), ('late', late), ('early', early), ('late_minutes', row['late']), ('early_minutes', row['early']), ('leave', int(row['status'] == 'Leave')), ('missing_out', int(row['status'] == 'Missing Check-Out')), ('worked', row['worked']), ('overtime', row['overtime']), ('scheduled', row['scheduled_hours'])]:
                employee[key] += amount
            for key, amount in [('present', present), ('absent', absent), ('late', late), ('early', early)]:
                department[key] += amount
            department['employees'].add(employee_id)
        employee_rows = sorted(employees.values(), key=lambda x: (not bool(x['code']), x['code'].casefold(), x['employee'].casefold(), x['id']))
        for employee in employee_rows:
            for key in ('worked', 'overtime', 'scheduled'):
                employee[key] = round(employee[key], 2)
            employee['difference'] = round(employee['worked'] - employee['scheduled'], 2)
            days = employee['present'] + employee['absent']
            employee['rate'] = round(employee['present'] * 100 / days, 1) if days else 0
        department_rows = []
        for department in departments.values():
            department['employees'] = len(department['employees'])
            days = department['present'] + department['absent']
            department['rate'] = round(department['present'] * 100 / days, 1) if days else 0
            department_rows.append(department)
        department_rows.sort(key=lambda x: (-x['absent'], x['name'].casefold(), x['id']))
        return {'employees': employee_rows, 'departments': department_rows}

    @api.model
    def get_dashboard_data(self, filters=None, page=1, limit=100):
        report = self._get_report(filters or {})
        report['analytics'] = self._get_analytics(report['rows'], report['date_from'], report['date_to'])
        page, limit = max(1, int(page)), min(500, max(1, int(limit)))
        report['rows'] = report['rows'][(page - 1) * limit:page * limit]
        report['page'], report['limit'] = page, limit
        return report

    @api.model
    def get_employee_details(self, filters, employee_id):
        self._check_access()
        employee_id = int(employee_id)
        employee = self.env['hr.employee'].browse(employee_id).exists()
        if not employee:
            raise UserError(_('Employee not found.'))
        detail_filters = dict(filters or {})
        detail_filters['employee_ids'], detail_filters['status'] = [employee_id], 'all'
        report = self._get_report(detail_filters)
        analytics = self._get_analytics(report['rows'], report['date_from'], report['date_to'])
        entry = next((item for item in analytics['employees'] if item['id'] == employee_id), False)
        return {'employee': entry or {'id': employee_id, 'code': employee.registration_number2 or '', 'employee': employee.name, 'department': employee.department_id.name or '', 'present': 0, 'absent': 0, 'leave': 0, 'late_minutes': 0, 'early_minutes': 0, 'missing_out': 0, 'worked': 0, 'overtime': 0, 'scheduled': 0, 'difference': 0, 'rate': 0}, 'rows': report['rows'], 'date_from': report['date_from'], 'date_to': report['date_to']}

    @staticmethod
    def _format_minutes(value):
        minutes = max(0, int(value or 0))
        hours, remaining = divmod(minutes, 60)
        return ('%sh %sm' % (hours, remaining)) if hours and remaining else ('%sh' % hours if hours else '%sm' % remaining)

    @api.model
    def export_excel(self, filters=None, report_mode='overview', department_id=False, employee_id=False):
        self._check_access()
        filters = dict(filters or {})
        report_mode = report_mode if report_mode in ('overview', 'department', 'employee', 'daily') else 'overview'
        department_id, employee_id = int(department_id) if department_id else False, int(employee_id) if employee_id else False
        if department_id:
            if not self.env['hr.department'].browse(department_id).exists():
                raise UserError(_('Department not found.'))
            selected = [int(x) for x in filters.get('department_ids', [])]
            if selected and department_id not in selected:
                raise AccessError(_('Department is outside the selected filters.'))
            filters['department_ids'] = [department_id]
        if employee_id:
            if not self.env['hr.employee'].browse(employee_id).exists():
                raise UserError(_('Employee not found.'))
            selected = [int(x) for x in filters.get('employee_ids', [])]
            if selected and employee_id not in selected:
                raise AccessError(_('Employee is outside the selected filters.'))
            filters['employee_ids'], filters['status'] = [employee_id], 'all'
        report = self._get_report(filters)
        analytics = self._get_analytics(report['rows'], report['date_from'], report['date_to'])
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet({'overview': 'Attendance Overview', 'department': 'Department Overview', 'employee': 'Employee Summary', 'daily': 'Daily Attendance'}[report_mode])
        sheet.hide_gridlines(2)
        sheet.set_tab_color('#327D87')
        title_fmt = workbook.add_format({'bold': True, 'font_size': 16, 'font_color': '#FFFFFF', 'bg_color': '#327D87', 'align': 'center', 'valign': 'vcenter'})
        heading_fmt = workbook.add_format({'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#354453', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        normal = workbook.add_format({'font_color': '#354453', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'border_color': '#E3EAF0'})
        alternate = workbook.add_format({'font_color': '#354453', 'bg_color': '#F4F8F9', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'border_color': '#E3EAF0'})
        date_fmt = workbook.add_format({'align': 'center', 'font_color': '#526476'})
        if report_mode == 'overview':
            headings = ['Metric', 'Value']
            s = report['summary']
            data = [['Total Employees', s['employees']], ['Present Days', s['present']], ['Absent Days', s['absent']], ['Late In', s['late']], ['Early Out', s['early']], ['Leave Days', s['leave']], ['Missing Check-Out', s['missing_out']], ['Scheduled Hours', s['scheduled_hours']], ['Worked Hours', s['worked_hours']], ['Overtime Hours', s['overtime_hours']], ['Hours Difference', s['hours_difference']], ['Attendance Rate (%)', s['attendance_rate']], ['Absence Rate (%)', s['absence_rate']]]
            widths = [36, 24]
        elif report_mode == 'department':
            headings = ['Department', 'Employees', 'Present Days', 'Absent Days', 'Late In', 'Early Out', 'Attendance Rate (%)']
            data = [[d['name'], d['employees'], d['present'], d['absent'], d['late'], d['early'], d['rate']] for d in analytics['departments']]
            widths = [38, 16, 18, 18, 17, 17, 24]
        elif report_mode == 'employee':
            headings = ['Employee Code', 'Employee', 'Department', 'Present', 'Absent', 'Leave', 'Late In', 'Early Out', 'Missing Out', 'Scheduled Hours', 'Worked Hours', 'Difference', 'Overtime Hours', 'Attendance Rate (%)']
            data = [[e['code'], e['employee'], e['department'], e['present'], e['absent'], e['leave'], self._format_minutes(e['late_minutes']), self._format_minutes(e['early_minutes']), e['missing_out'], e['scheduled'], e['worked'], e['difference'], e['overtime'], e['rate']] for e in analytics['employees']]
            widths = [18, 34, 30, 13, 13, 13, 18, 18, 17, 20, 18, 17, 20, 23]
        else:
            headings = ['Date', 'Day', 'Employee Code', 'Employee', 'Department', 'Shift Name', 'Shift Start - End', 'Check In', 'Check Out', 'Late In', 'Early Out', 'Worked Hours', 'Overtime Hours', 'Status', 'Remarks']
            data = [[r['date'], r['day'], r['code'], r['employee'], r['department'], r['shift'], r['shift_time'], r['check_in'], r['check_out'], self._format_minutes(r['late']), self._format_minutes(r['early']), r['worked'], r['overtime'], r['status'], r['remarks']] for r in report['rows']]
            widths = [14, 15, 18, 34, 30, 32, 20, 16, 16, 18, 18, 18, 19, 25, 44]
        for col, width in enumerate(widths):
            sheet.set_column(col, col, width)
        sheet.merge_range(0, 0, 1, len(headings) - 1, sheet.name.upper(), title_fmt)
        sheet.merge_range(2, 0, 2, len(headings) - 1, '%s TO %s' % (report['date_from'], report['date_to']), date_fmt)
        sheet.set_row(4, 34)
        for col, heading in enumerate(headings):
            sheet.write(4, col, heading, heading_fmt)
        sheet.freeze_panes(5, 1 if report_mode in ('overview', 'department') else 3)
        for index, values in enumerate(data, 5):
            fmt = alternate if index % 2 else normal
            for col, value in enumerate(values):
                sheet.write(index, col, value if value is not None else '', fmt)
            sheet.set_row(index, 26)
        if data:
            sheet.autofilter(4, 0, 4 + len(data), len(headings) - 1)
        workbook.close()
        attachment = self.env['ir.attachment'].create({'name': 'Attendance_%s_%s_%s.xlsx' % (report_mode.title(), report['date_from'], report['date_to']), 'type': 'binary', 'datas': base64.b64encode(output.getvalue()), 'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'res_model': 'res.users', 'res_id': self.env.uid})
        return {'url': '/web/content/%s?download=true' % attachment.id}