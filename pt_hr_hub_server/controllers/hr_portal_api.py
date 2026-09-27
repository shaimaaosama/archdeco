# -*- coding: utf-8 -*-

import base64
import binascii
import logging
from odoo import http, _, fields
from odoo.http import request
from odoo.addons.muk_rest import core
from odoo.addons.muk_rest.tools.http import build_route
from odoo.exceptions import ValidationError, AccessError
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)

class HrPortalHubController(http.Controller):

    def _get_faceio_app_settings(self):
        config = request.env['ir.config_parameter'].sudo()
        encrypted_secret = config.get_param('pt_hr_hub_server.faceio_secret_key_encrypted')
        secret_key = False

        if encrypted_secret:
            secret_key = request.env['res.config.settings']._decrypt_secret(encrypted_secret)

        return {
            'faceio_enabled': str(config.get_param('pt_hr_hub_server.faceio_enabled') or '').lower() in ('1', 'true', 'yes'),
            'faceio_public_id': config.get_param('pt_hr_hub_server.faceio_app_public_id') or False,
            'faceio_secret_key': secret_key or False,
        }

    def _get_employee(self):
        """Helper to get the employee linked to the current user.

        Works for both internal users (employee_id computed field) and portal
        users whose employee record has user_id set to this user.
        """
        # For internal users the ORM computed field resolves quickly.
        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', request.uid)], limit=1
        )
        if not employee:
            raise ValidationError(
                _("No employee record is linked to your user account (uid=%s). "
                  "Please ask an HR administrator to set the 'Related User' field "
                  "on your employee profile.") % request.uid
            )
        return employee

    def _resolve_activity_assignee(self, params):
        employee_id = params.get('employee_id')
        user_id = params.get('user_id')

        if employee_id:
            employee = request.env['hr.employee'].sudo().browse(int(employee_id))
            if not employee.exists():
                raise ValidationError(_("Employee not found."))
            if not employee.user_id:
                raise ValidationError(_("Selected employee has no linked user."))
            return employee, employee.user_id

        if user_id:
            user = request.env['res.users'].sudo().browse(int(user_id))
            if not user.exists():
                raise ValidationError(_("User not found."))
            employee = user.employee_id or request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            return employee, user

        raise ValidationError(_("employee_id or user_id is required."))

    def _serialize_task(self, activity, today=False):
        today = today or fields.Date.today()
        task_state = 'in_progress' if activity.date_deadline and activity.date_deadline <= today else 'pending'
        return {
            'id': activity.id,
            'summary': activity.summary,
            'note': activity.note,
            'activity_type': activity.activity_type_id.name,
            'date_deadline': fields.Date.to_string(activity.date_deadline) if activity.date_deadline else False,
            'res_model': activity.res_model,
            'res_id': activity.res_id,
            'res_name': activity.res_name,
            'state': task_state,
        }

    def _serialize_meeting(self, event):
        start_dt = event.start
        stop_dt = event.stop

        date_value = fields.Date.to_string(start_dt.date()) if start_dt else False
        time_value = False
        if start_dt and stop_dt:
            time_value = "%s - %s" % (
                fields.Datetime.to_string(start_dt)[11:16],
                fields.Datetime.to_string(stop_dt)[11:16],
            )
        elif start_dt:
            time_value = fields.Datetime.to_string(start_dt)[11:16]

        agenda = html2plaintext(event.description) if event.description else False
        meeting_url = getattr(event, 'videocall_location', False) or getattr(event, 'access_token', False) or False

        return {
            'id': event.id,
            'name': event.name,
            'time': time_value,
            'date': date_value,
            'url': meeting_url,
            'meeting_agenda': agenda,
            'participants': [partner.name for partner in event.partner_ids],
            'notes': agenda,
        }

    def _serialize_notification(self, notification):
        message = notification.mail_message_id
        return {
            'id': notification.id,
            'title': message.subject or message.record_name or _('Notification'),
            'body': html2plaintext(message.body) if message.body else False,
            'date': fields.Datetime.to_string(message.date) if message.date else False,
            'is_read': bool(getattr(notification, 'is_read', False)),
            'model': message.model,
            'res_id': message.res_id,
        }

    def _as_bool(self, value, default=False):
        if value in (None, ''):
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ('1', 'true', 'yes', 'y', 'on')

    def _serialize_payslip(self, slip):
        net_line = slip.line_ids.filtered(lambda line: line.code == 'NET')[:1]
        if net_line:
            full_salary = net_line.total
        elif hasattr(slip, 'net_wage'):
            full_salary = slip.net_wage
        else:
            full_salary = 0.0

        paid_on_date = False
        if hasattr(slip, 'date') and slip.date:
            paid_on_date = slip.date
        elif slip.move_id and slip.move_id.date:
            paid_on_date = slip.move_id.date

        period_date = slip.date_to or slip.date_from or paid_on_date
        period_month = False
        period_year = False
        if period_date:
            period_as_date = fields.Date.from_string(period_date)
            period_month = period_as_date.month
            period_year = period_as_date.year

        return {
            'id': slip.id,
            'employee_id': slip.employee_id.id,
            'employee_name': slip.employee_id.name,
            'number': getattr(slip, 'number', False),
            'name': slip.name,
            'date_from': fields.Date.to_string(slip.date_from) if slip.date_from else False,
            'date_to': fields.Date.to_string(slip.date_to) if slip.date_to else False,
            'month': period_month,
            'year': period_year,
            'full_salary': full_salary,
            'paid_on_date': fields.Date.to_string(paid_on_date) if paid_on_date else False,
            'state': slip.state,
        }

    def _get_user_permissions(self, employee=False):
        """Return a dict of boolean permissions for each API capability."""
        user = request.env.user
        employee = employee or request.env['hr.employee'].sudo().search(
            [('user_id', '=', request.uid)], limit=1
        )

        is_hr_manager = user.has_group('hr.group_hr_manager')

        payroll_group = request.env.ref('hr_payroll.group_hr_payroll_manager', raise_if_not_found=False)
        is_payroll_manager = bool(payroll_group and payroll_group in user.groups_id)

        leave_manager_group = request.env.ref('hr_holidays.group_hr_holidays_manager', raise_if_not_found=False)
        is_leave_manager = bool(leave_manager_group and leave_manager_group in user.groups_id) or is_hr_manager

        expense_manager_group = request.env.ref('hr_expense.group_hr_expense_manager', raise_if_not_found=False)
        is_expense_manager = bool(expense_manager_group and expense_manager_group in user.groups_id) or is_hr_manager

        has_employee = bool(employee)
        require_face_attendance = bool(
            employee
            and 'require_face_attendance' in employee._fields
            and employee.require_face_attendance
        )

        can_manage_payroll = is_hr_manager or is_payroll_manager
        can_manage = is_hr_manager or is_leave_manager or is_expense_manager or can_manage_payroll

        return {
            # Employee self-service
            'submit_leave': has_employee,
            'submit_expense': has_employee,
            'submit_attendance': has_employee,
            'view_my_payslips': has_employee,
            'view_my_payslip_detail': has_employee,
            'view_my_leaves': has_employee,
            'view_my_expenses': has_employee,
            'view_my_tasks': has_employee,
            'view_my_meetings': has_employee,
            'view_my_dashboard': has_employee,
            'require_face_attendance': require_face_attendance,
            # Manager / HR access
            'approve_expenses': is_expense_manager,
            'approve_leaves': is_leave_manager,
            'approve_requests': can_manage,
            'list_employees': can_manage_payroll,
            'view_payroll_payslips': can_manage_payroll,
            'view_payroll_payslip_detail': can_manage_payroll,
            'view_payroll_payslip_months': can_manage_payroll,
            'assign_tasks': can_manage,
            'view_approvals': can_manage,
        }

    def _ensure_payroll_access(self):
        is_hr_manager = request.env.user.has_group('hr.group_hr_manager')
        payroll_group = request.env.ref('hr_payroll.group_hr_payroll_manager', raise_if_not_found=False)
        is_payroll_manager = bool(payroll_group and payroll_group in request.env.user.groups_id)
        if not (is_hr_manager or is_payroll_manager):
            raise AccessError(_("You are not authorized to view payroll payslips."))

    def _get_payslip_from_params(self, employee_id, params, allow_cross_employee=False):
        payslip_id_value = params.get('id') or params.get('payslip_id')
        if payslip_id_value not in (None, ''):
            try:
                payslip_id = int(payslip_id_value)
            except Exception:
                raise ValidationError(_('Payslip id must be a valid integer.'))
            slip = request.env['hr.payslip'].sudo().browse(payslip_id)
            if not slip.exists():
                raise ValidationError(_('Payslip not found.'))
            if not allow_cross_employee and slip.employee_id.id != employee_id:
                raise AccessError(_('You are not authorized to view this payslip.'))
            if employee_id and slip.employee_id.id != employee_id:
                raise ValidationError(_('The provided payslip does not belong to the selected employee.'))
            return slip

        month_value = params.get('month')
        year_value = params.get('year')
        if month_value in (None, '') or year_value in (None, ''):
            raise ValidationError(_('month and year are required when payslip_id is not provided.'))

        try:
            month = int(month_value)
            year = int(year_value)
        except Exception:
            raise ValidationError(_('month and year must be valid integers.'))
        if month < 1 or month > 12:
            raise ValidationError(_('month must be between 1 and 12.'))
        if year < 1900 or year > 9999:
            raise ValidationError(_('year must be a valid 4-digit year.'))

        month_start = fields.Date.from_string('%04d-%02d-01' % (year, month))
        if month == 12:
            month_end = fields.Date.from_string('%04d-12-31' % year)
        else:
            next_month_start = fields.Date.from_string('%04d-%02d-01' % (year, month + 1))
            month_end = fields.Date.subtract(next_month_start, days=1)

        slip = request.env['hr.payslip'].sudo().search([
            ('employee_id', '=', employee_id),
            ('date_from', '<=', fields.Date.to_string(month_end)),
            ('date_to', '>=', fields.Date.to_string(month_start)),
        ], order='date_to desc, id desc', limit=1)
        if not slip:
            raise ValidationError(_('No payslip found for month %(month)s and year %(year)s.') % {
                'month': month,
                'year': year,
            })
        return slip

    def _serialize_payslip_detail(self, slip):
        all_lines = []
        earnings_lines = []
        deduction_lines = []
        net_line = False
        earnings_total = 0.0
        deductions_total = 0.0
        net_total = 0.0

        for line in slip.line_ids.sorted(lambda line: (line.sequence, line.id)):
            line_total = line.total or 0.0
            if line.code == 'NET':
                net_total = line_total
                line_group = 'net'
            elif line_total < 0:
                deductions_total += abs(line_total)
                line_group = 'deduction'
            else:
                earnings_total += line_total
                line_group = 'earning'

            line_data = {
                'id': line.id,
                'name': line.name,
                'code': line.code,
                'category': line.category_id.name if line.category_id else False,
                'quantity': line.quantity,
                'amount': line.amount,
                'rate': line.rate,
                'total': line_total,
                'group': line_group,
            }
            all_lines.append(line_data)
            if line_group == 'earning':
                earnings_lines.append(line_data)
            elif line_group == 'deduction':
                deduction_lines.append(line_data)
            elif line_group == 'net':
                net_line = line_data

        payload = self._serialize_payslip(slip)
        payload.update({
            'company_name': slip.company_id.name if slip.company_id else False,
            'struct_name': slip.struct_id.name if slip.struct_id else False,
            'currency': slip.company_id.currency_id.name if slip.company_id and slip.company_id.currency_id else False,
            'totals': {
                'earnings': earnings_total,
                'deductions': deductions_total,
                'net': net_total,
            },
            'lines': all_lines,
            'earnings_lines': earnings_lines,
            'deduction_lines': deduction_lines,
            'net_line': net_line,
        })
        return payload

    def _create_expense_receipt_attachment(self, expense, params):
        receipt_image = (
            params.get('receipt_image')
            or params.get('receipt_image_base64')
            or params.get('bill_image')
            or params.get('receipt')
        )
        if not receipt_image:
            return False

        receipt_image = str(receipt_image).strip()
        if ',' in receipt_image and ';base64' in receipt_image:
            receipt_image = receipt_image.split(',', 1)[1]

        try:
            base64.b64decode(receipt_image, validate=True)
        except (binascii.Error, ValueError):
            raise ValidationError(_('Receipt image must be a valid base64-encoded file.'))

        filename = params.get('receipt_filename') or params.get('bill_filename') or '%s-receipt.png' % expense.id
        mimetype = params.get('receipt_mimetype') or params.get('bill_mimetype') or 'image/png'

        attachment = request.env['ir.attachment'].sudo().create({
            'name': filename,
            'datas': receipt_image,
            'res_model': 'hr.expense',
            'res_id': expense.id,
            'mimetype': mimetype,
        })

        if hasattr(expense, 'message_main_attachment_id') and not expense.message_main_attachment_id:
            expense.message_main_attachment_id = attachment.id

        return attachment

    # --- EXPENSES ---

    @core.http.rest_route(
        routes=build_route("/hr_hub/my/expenses"),
        methods=["GET"],
        protected=True,
        docs={
            "tags": ["HR Hub"],
            "summary": "Get My Expenses",
            "description": "Return expense records for the authenticated employee.",
        },
    )
    def get_my_expenses(self, **kw):
        employee = self._get_employee()
        expenses = request.env['hr.expense'].sudo().search([('employee_id', '=', employee.id)])
        return request.make_json_response([{
            'id': exp.id,
            'name': exp.name,
            'date': exp.date,
            'amount': exp.unit_amount * exp.quantity,
            'state': exp.state,
            'category': exp.product_id.name,
        } for exp in expenses])

    @core.http.rest_route(
        routes=build_route("/hr_hub/my/expense/submit"),
        methods=["POST"],
        protected=True,
        docs={
            "tags": ["HR Hub"],
            "summary": "Submit My Expense",
            "description": "Create an expense for the authenticated employee and optionally submit it in an expense sheet.",
        },
    )
    def post_my_expense(self, **kw):
        params = kw or request.jsonrequest or request.params
        employee = self._get_employee()
        
        vals = {
            'name': params.get('name'),
            'employee_id': employee.id,
            'product_id': int(params.get('product_id')),
            'unit_amount': float(params.get('amount', 0.0)),
            'quantity': float(params.get('quantity', 1.0)),
            'date': params.get('date') or fields.Date.today(),
        }
        expense = request.env['hr.expense'].sudo().create(vals)
        attachment = self._create_expense_receipt_attachment(expense, params)
        
        # Automatically create a sheet and submit if requested
        if self._as_bool(params.get('submit', True), default=True):
            sheet = request.env['hr.expense.sheet'].sudo().create({
                'name': expense.name,
                'employee_id': employee.id,
                'expense_line_ids': [(6, 0, [expense.id])],
            })
            sheet.action_submit_sheet()
            
        return {
            'success': True,
            'id': expense.id,
            'receipt_attachment_id': attachment.id if attachment else False,
        }

    # --- LEAVES (TIME OFF) ---

    @core.http.rest_route(
        routes=build_route("/hr_hub/my/leaves"),
        methods=["GET"],
        protected=True,
        docs={
            "tags": ["HR Hub"],
            "summary": "Get My Leaves",
            "description": "Return leave requests for the authenticated employee.",
        },
    )
    def get_my_leaves(self, **kw):
        employee = self._get_employee()
        leaves = request.env['hr.leave'].sudo().search([('employee_id', '=', employee.id)])
        return request.make_json_response([{
            'id': l.id,
            'type': l.holiday_status_id.name,
            'date_from': l.date_from,
            'date_to': l.date_to,
            'number_of_days': l.number_of_days,
            'state': l.state,
        } for l in leaves])

    @core.http.rest_route(
        routes=build_route("/hr_hub/my/tasks"),
        methods=["GET"],
        protected=True,
        docs={
            "tags": ["HR Hub"],
            "summary": "Get My Tasks",
            "description": "Return activities assigned to the authenticated user.",
        },
    )
    def get_my_tasks(self, **kw):
        activities = request.env['mail.activity'].sudo().search(
            [('user_id', '=', request.uid)],
            order='date_deadline asc, id desc',
        )
        return request.make_json_response([{
            'id': activity.id,
            'summary': activity.summary,
            'note': activity.note,
            'activity_type': activity.activity_type_id.name,
            'date_deadline': fields.Date.to_string(activity.date_deadline) if activity.date_deadline else False,
            'res_model': activity.res_model,
            'res_id': activity.res_id,
            'res_name': activity.res_name,
            'state': 'overdue' if activity.date_deadline and activity.date_deadline < fields.Date.today() else 'planned',
        } for activity in activities])

    @core.http.rest_route(
        routes=build_route("/hr_hub/my/tasks/summary"),
        methods=["GET"],
        protected=True,
        docs={
            "tags": ["HR Hub"],
            "summary": "Get My Tasks Summary",
            "description": "Return my tasks grouped as pending, in progress, and completed.",
        },
    )
    def get_my_tasks_summary(self, **kw):
        today = fields.Date.today()
        activities = request.env['mail.activity'].sudo().search(
            [('user_id', '=', request.uid)],
            order='date_deadline asc, id desc',
        )

        pending_tasks = []
        tasks_in_progress = []

        for activity in activities:
            task_payload = {
                'id': activity.id,
                'summary': activity.summary,
                'note': activity.note,
                'activity_type': activity.activity_type_id.name,
                'date_deadline': fields.Date.to_string(activity.date_deadline) if activity.date_deadline else False,
                'res_model': activity.res_model,
                'res_id': activity.res_id,
                'res_name': activity.res_name,
            }

            # In-progress tasks are actionable now (today/overdue); future/undated are pending.
            if activity.date_deadline and activity.date_deadline <= today:
                task_payload['state'] = 'in_progress'
                tasks_in_progress.append(task_payload)
            else:
                task_payload['state'] = 'pending'
                pending_tasks.append(task_payload)

        return request.make_json_response({
            'pending_tasks': pending_tasks,
            'tasks_in_progress': tasks_in_progress,
            # mail.activity records are removed when marked done, so this endpoint returns 0 by design.
            'completed_tasks': [],
            'counts': {
                'pending_tasks': len(pending_tasks),
                'tasks_in_progress': len(tasks_in_progress),
                'completed_tasks': 0,
            },
        })

    @core.http.rest_route(
        routes=build_route("/hr_hub/my/meetings"),
        methods=["GET"],
        protected=True,
        docs={
            "tags": ["HR Hub"],
            "summary": "Get My Meetings",
            "description": "Return meetings/calendar events where the authenticated user is an attendee.",
        },
    )
    def get_my_meetings(self, **kw):
        params = kw or request.params

        from_value = params.get('from')
        to_value = params.get('to')
        limit_value = params.get('limit')
        upcoming_only_value = str(params.get('upcoming_only', '')).strip().lower()

        from_dt = False
        to_dt = False
        if from_value:
            try:
                from_dt = fields.Datetime.from_string(from_value)
            except Exception:
                raise ValidationError(_("Invalid 'from' datetime format. Use YYYY-MM-DD HH:MM:SS."))
        if to_value:
            try:
                to_dt = fields.Datetime.from_string(to_value)
            except Exception:
                raise ValidationError(_("Invalid 'to' datetime format. Use YYYY-MM-DD HH:MM:SS."))
        if from_dt and to_dt and from_dt > to_dt:
            raise ValidationError(_("'from' must be earlier than or equal to 'to'."))

        limit = False
        if limit_value not in (None, ''):
            try:
                limit = int(limit_value)
            except Exception:
                raise ValidationError(_("Invalid 'limit'. It must be a positive integer."))
            if limit <= 0:
                raise ValidationError(_("Invalid 'limit'. It must be a positive integer."))

        upcoming_only = upcoming_only_value in ('1', 'true', 'yes', 'y')

        # Include events where the user is invited through partner attendees.
        partner_id = request.env.user.partner_id.id
        domain = [('partner_ids', 'in', [partner_id])]
        if from_dt:
            domain.append(('start', '>=', fields.Datetime.to_string(from_dt)))
        if to_dt:
            domain.append(('start', '<=', fields.Datetime.to_string(to_dt)))
        if upcoming_only and not from_dt:
            domain.append(('start', '>=', fields.Datetime.now()))

        events = request.env['calendar.event'].sudo().search(
            domain,
            order='start asc, id desc',
            limit=limit,
        )

        return request.make_json_response([{
            'id': event.id,
            'name': event.name,
            'start': fields.Datetime.to_string(event.start) if event.start else False,
            'stop': fields.Datetime.to_string(event.stop) if event.stop else False,
            'allday': event.allday,
            'location': event.location,
            'description': event.description,
            'organizer': event.user_id.name,
            'attendees': [partner.name for partner in event.partner_ids],
        } for event in events])

    @core.http.rest_route(
        routes=build_route("/hr_hub/my/dashboard"),
        methods=["GET"],
        protected=True,
        docs={
            "tags": ["HR Hub"],
            "summary": "Get My Dashboard",
            "description": "Return dashboard data for mobile app including task summary, meetings, tasks, and notifications.",
        },
    )
    def get_my_dashboard(self, **kw):
        params = kw or request.params
        today = fields.Date.today()
        employee = self._get_employee()
        app_settings = self._get_faceio_app_settings()

        activities = request.env['mail.activity'].sudo().search(
            [('user_id', '=', request.uid)],
            order='date_deadline asc, id desc',
        )
        tasks_list = [self._serialize_task(activity, today=today) for activity in activities]

        tasks_in_progress_count = len([task for task in tasks_list if task.get('state') == 'in_progress'])
        # mail.activity records are removed when marked as done, so completed count is 0 by design.
        completed_tasks_count = 0

        meeting_limit = int(params.get('meetings_limit', 20)) if str(params.get('meetings_limit', '')).isdigit() else 20
        notification_limit = int(params.get('notifications_limit', 20)) if str(params.get('notifications_limit', '')).isdigit() else 20

        partner_id = request.env.user.partner_id.id
        meetings = request.env['calendar.event'].sudo().search(
            [('partner_ids', 'in', [partner_id])],
            order='start asc, id desc',
            limit=meeting_limit,
        )

        notifications = request.env['mail.notification'].sudo().search(
            [
                ('res_partner_id', '=', partner_id),
                ('mail_message_id', '!=', False),
            ],
            order='id desc',
            limit=notification_limit,
        )

        return request.make_json_response({
            'employee_id': employee.id,
            'display_name': employee.display_name,
            'name': employee.name,
            'job_position': employee.job_title or (employee.job_id.name if employee.job_id else False),
            'app_settings': app_settings,
            'tasks_summary': {
                'tasks_in_progress': tasks_in_progress_count,
                'completed_tasks': completed_tasks_count,
            },
            'meetings_list': [self._serialize_meeting(event) for event in meetings],
            'tasks_list': tasks_list,
            'notifications_list': [self._serialize_notification(notification) for notification in notifications],
            'permissions': self._get_user_permissions(employee=employee),
        })

    @core.http.rest_route(
        routes=build_route("/hr_hub/my/tasks/done"),
        methods=["POST"],
        protected=True,
        docs={
            "tags": ["HR Hub"],
            "summary": "Mark My Task Done",
            "description": "Mark an assigned activity as done using activity id and optional feedback.",
        },
    )
    def post_my_task_done(self, **kw):
        params = kw or request.jsonrequest or request.params
        activity_id = int(params.get('id', 0))
        if not activity_id:
            raise ValidationError(_("Activity id is required."))

        activity = request.env['mail.activity'].sudo().browse(activity_id)
        if not activity.exists():
            raise ValidationError(_("Activity not found."))
        if activity.user_id.id != request.uid:
            raise AccessError(_("You are not authorized to update this activity."))

        feedback = params.get('feedback') or params.get('note') or _("Completed from mobile.")
        if hasattr(activity, 'action_feedback'):
            activity.action_feedback(feedback=feedback)
        elif hasattr(activity, 'action_done'):
            activity.action_done()
        else:
            activity.unlink()

        return request.make_json_response({'success': True, 'id': activity_id})

    @core.http.rest_route(
        routes=build_route("/hr_hub/my/leave/request"),
        methods=["POST"],
        protected=True,
        docs={
            "tags": ["HR Hub"],
            "summary": "Submit Leave Request",
            "description": "Create a leave request for the authenticated employee.",
        },
    )
    def post_my_leave(self, **kw):
        params = kw or request.params
        employee = self._get_employee()
        
        vals = {
            'holiday_status_id': int(params.get('holiday_status_id')),
            'employee_id': employee.id,
            'request_date_from': params.get('date_from'),
            'request_date_to': params.get('date_to'),
            'name': params.get('description', ''),
        }
        leave = request.env['hr.leave'].sudo().create(vals)
        # Odoo 18 leaves are often auto-submitted or need action_confirm
        if hasattr(leave, 'action_confirm'):
            leave.action_confirm()
            
        return {'success': True, 'id': leave.id}

    @core.http.rest_route(
        routes=build_route('/hr_hub/my/payslips'),
        methods=['GET'],
        protected=True,
        docs={
            'tags': ['HR Hub'],
            'summary': 'Get My Payslips',
            'description': 'Return payslips for the authenticated employee.',
        },
    )
    def get_my_payslips(self, **kw):
        employee = self._get_employee()
        payslips = request.env['hr.payslip'].sudo().search(
            [('employee_id', '=', employee.id)],
            order='date_to desc, id desc',
        )
        return request.make_json_response([self._serialize_payslip(slip) for slip in payslips])

    @core.http.rest_route(
        routes=build_route('/hr_hub/my/payslip'),
        methods=['GET'],
        protected=True,
        docs={
            'tags': ['HR Hub'],
            'summary': 'Get My Payslip By Month',
            'description': 'Return one authenticated employee payslip in JSON detail for a given month and year, or by payslip id.',
        },
    )
    def get_my_payslip(self, **kw):
        params = kw or request.params
        employee = self._get_employee()
        slip = self._get_payslip_from_params(employee.id, params)
        return request.make_json_response(self._serialize_payslip_detail(slip))

    # --- MANAGER APPROVALS ---

    @core.http.rest_route(
        routes=build_route('/hr_hub/payroll/payslip'),
        methods=['GET'],
        protected=True,
        docs={
            'tags': ['HR Hub'],
            'summary': 'Get Employee Payslip Detail',
            'description': 'Return one employee payslip in JSON detail for a given employee and month/year, or by payslip id.',
        },
    )
    def get_payroll_payslip(self, **kw):
        params = kw or request.params
        self._ensure_payroll_access()

        employee_id_value = params.get('employee_id')
        payslip_id_value = params.get('id') or params.get('payslip_id')
        if employee_id_value in (None, '') and payslip_id_value in (None, ''):
            raise ValidationError(_('employee_id is required when payslip_id is not provided.'))

        employee_id = False
        if employee_id_value not in (None, ''):
            try:
                employee_id = int(employee_id_value)
            except Exception:
                raise ValidationError(_('employee_id must be a valid integer.'))
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            if not employee.exists():
                raise ValidationError(_('Employee not found.'))

        slip = self._get_payslip_from_params(employee_id, params, allow_cross_employee=True)
        return request.make_json_response(self._serialize_payslip_detail(slip))

    @core.http.rest_route(
        routes=build_route("/hr_hub/payroll/payslips"),
        methods=["GET"],
        protected=True,
        docs={
            "tags": ["HR Hub"],
            "summary": "Get Employee Payslips",
            "description": "Return all employee payslips with month/year, full salary, and paid-on date.",
        },
    )
    def get_payroll_payslips(self, **kw):
        is_hr_manager = request.env.user.has_group('hr.group_hr_manager')
        payroll_group = request.env.ref('hr_payroll.group_hr_payroll_manager', raise_if_not_found=False)
        is_payroll_manager = bool(payroll_group and payroll_group in request.env.user.groups_id)
        if not (is_hr_manager or is_payroll_manager):
            raise AccessError(_("You are not authorized to view payroll payslips."))

        payslips = request.env['hr.payslip'].sudo().search([], order='date_to desc, id desc')
        return request.make_json_response([self._serialize_payslip(slip) for slip in payslips])

    @core.http.rest_route(
        routes=build_route('/hr_hub/manager/employees'),
        methods=['GET'],
        protected=True,
        docs={
            'tags': ['HR Hub'],
            'summary': 'List All Employees',
            'description': 'Return all active employees for manager selection before viewing payslips.',
        },
    )
    def get_manager_employees(self, **kw):
        self._ensure_payroll_access()
        employees = request.env['hr.employee'].sudo().search(
            [('active', '=', True)],
            order='name asc',
        )
        result = []
        for emp in employees:
            result.append({
                'id': emp.id,
                'name': emp.name,
                'job_title': emp.job_title or False,
                'department': emp.department_id.name if emp.department_id else False,
                'work_email': emp.work_email or False,
            })
        return request.make_json_response(result)

    @core.http.rest_route(
        routes=build_route('/hr_hub/payroll/payslip/months'),
        methods=['GET'],
        protected=True,
        docs={
            'tags': ['HR Hub'],
            'summary': 'List Available Payslip Months For Employee',
            'description': 'Return all payslip periods available for a given employee. Pass employee_id as query param.',
        },
    )
    def get_payroll_payslip_months(self, **kw):
        params = kw or request.params
        self._ensure_payroll_access()

        employee_id_value = params.get('employee_id')
        if employee_id_value in (None, ''):
            raise ValidationError(_('employee_id is required.'))
        try:
            employee_id = int(employee_id_value)
        except Exception:
            raise ValidationError(_('employee_id must be a valid integer.'))

        employee = request.env['hr.employee'].sudo().browse(employee_id)
        if not employee.exists():
            raise ValidationError(_('Employee not found.'))

        payslips = request.env['hr.payslip'].sudo().search(
            [('employee_id', '=', employee_id)],
            order='date_to desc, id desc',
        )
        result = []
        for slip in payslips:
            date_from = slip.date_from
            date_to = slip.date_to
            result.append({
                'id': slip.id,
                'name': slip.name or False,
                'month': date_from.month if date_from else False,
                'year': date_from.year if date_from else False,
                'date_from': str(date_from) if date_from else False,
                'date_to': str(date_to) if date_to else False,
                'state': slip.state,
            })
        return request.make_json_response(result)

    @core.http.rest_route(
        routes=build_route("/hr_hub/manager/approvals"),
        methods=["GET"],
        protected=True,
        docs={
            "tags": ["HR Hub"],
            "summary": "Get Manager Approvals",
            "description": "Return pending leave and expense approvals for the current manager.",
        },
    )
    def get_manager_approvals(self, **kw):
        employee = self._get_employee()
        
        # Pending Expenses
        pending_expenses = request.env['hr.expense.sheet'].sudo().search([
            ('state', '=', 'submit'),
            ('user_id', '=', request.uid) # Odoo often assigns the sheet to the user
        ])
        # If no user_id, check by manager_id on employee
        if not pending_expenses:
             pending_expenses = request.env['hr.expense.sheet'].sudo().search([
                ('state', '=', 'submit'),
                ('employee_id.parent_id', '=', employee.id)
            ])

        # Pending Leaves
        pending_leaves = request.env['hr.leave'].sudo().search([
            ('state', '=', 'confirm'),
            ('employee_id.parent_id', '=', employee.id)
        ])
        
        return {
            'expenses': [{
                'id': s.id,
                'employee': s.employee_id.name,
                'name': s.name,
                'total_amount': s.total_amount,
            } for s in pending_expenses],
            'leaves': [{
                'id': l.id,
                'employee': l.employee_id.name,
                'type': l.holiday_status_id.name,
                'date_from': l.date_from,
                'date_to': l.date_to,
                'days': l.number_of_days,
            } for l in pending_leaves]
        }

    @core.http.rest_route(
        routes=build_route("/hr_hub/manager/tasks/assign"),
        methods=["POST"],
        protected=True,
        docs={
            "tags": ["HR Hub"],
            "summary": "Assign Task",
            "description": "Create an activity for an employee (via employee_id) or user (via user_id).",
        },
    )
    def post_manager_assign_task(self, **kw):
        params = kw or request.jsonrequest or request.params
        manager_employee = self._get_employee()
        target_employee, target_user = self._resolve_activity_assignee(params)

        if not request.env.user.has_group('hr.group_hr_manager'):
            if target_employee:
                if target_employee.parent_id != manager_employee and target_employee.id != manager_employee.id:
                    raise AccessError(_("You are not authorized to assign tasks to this employee."))
            elif target_user.id != request.uid:
                raise AccessError(_("You are not authorized to assign tasks to this user."))

        res_model = params.get('res_model')
        res_id = int(params.get('res_id', 0))
        if not res_model or not res_id:
            raise ValidationError(_("res_model and res_id are required."))

        try:
            target_record = request.env[res_model].sudo().browse(res_id)
        except Exception:
            raise ValidationError(_("Invalid model."))
        if not target_record.exists():
            raise ValidationError(_("Target record not found."))

        model_ref = request.env['ir.model'].sudo().search([('model', '=', res_model)], limit=1)
        if not model_ref:
            raise ValidationError(_("Model metadata not found."))

        activity_type_id = int(params.get('activity_type_id', 0))
        if activity_type_id:
            activity_type = request.env['mail.activity.type'].sudo().browse(activity_type_id)
            if not activity_type.exists():
                raise ValidationError(_("Activity type not found."))
        else:
            activity_type = request.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            if not activity_type:
                raise ValidationError(_("Default To-Do activity type not found."))

        activity = request.env['mail.activity'].sudo().create({
            'activity_type_id': activity_type.id,
            'summary': params.get('summary') or params.get('title') or _("Task"),
            'note': params.get('note') or False,
            'date_deadline': params.get('date_deadline') or fields.Date.today(),
            'res_model_id': model_ref.id,
            'res_id': res_id,
            'user_id': target_user.id,
        })

        return request.make_json_response({
            'success': True,
            'id': activity.id,
            'assigned_user_id': target_user.id,
            'assigned_employee_id': target_employee.id if target_employee else False,
        })

    @core.http.rest_route(
        routes=build_route("/hr_hub/manager/approve"),
        methods=["POST"],
        protected=True,
        docs={
            "tags": ["HR Hub"],
            "summary": "Approve Request",
            "description": "Approve a pending leave or expense sheet by model and record id.",
        },
    )
    def post_manager_approve(self, **kw):
        params = kw or request.params
        res_id = int(params.get('id'))
        res_model = params.get('model')
        employee = self._get_employee()
        
        record = request.env[res_model].sudo().browse(res_id)
        if not record.exists():
             raise ValidationError(_("Record not found."))

        # Basic security: Check if current employee is the manager
        target_employee = record.employee_id
        if target_employee.parent_id != employee and record.create_uid.id != request.uid:
            # We allow approve if manager or if it's a test? No, let's be strict
            # Some Odoo configs use expense_manager_id
            if hasattr(target_employee, 'expense_manager_id') and target_employee.expense_manager_id == request.env.user:
                pass
            else:
                raise AccessError(_("You are not authorized to approve this request."))

        if res_model == 'hr.expense.sheet':
            record.action_approve_expense_sheets()
        elif res_model == 'hr.leave':
            record.action_approve()
            
        return {'success': True}
