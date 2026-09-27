import uuid
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError, AccessDenied, UserError
import pytz

from odoo.addons.resource.models.utils import float_to_time, HOURS_PER_DAY
from pytz import timezone, UTC
from datetime import datetime, time, timedelta, date
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)

class HolidaysRequest(models.Model):
    _name = 'hr.leave'
    _inherit = ['hr.leave','mail.thread.main.attachment','portal.mixin', 'mail.thread', 'mail.activity.mixin']
    
    def _get_default_access_token(self):
        return str(uuid.uuid4())
    
    access_url = fields.Char('Portal Access URL', compute='_compute_access_url',help='Contract Portal URL')
    access_token = fields.Char('Access Token', default=lambda self: self._get_default_access_token(), copy=False)
    
    def _compute_access_url(self):
        for leave in self:
            leave.access_url = '/my/leave/%s' % leave.id
    
    def _portal_ensure_token(self):
        """ Get the current record access token """
        if not self.access_token:
            self.sudo().write({'access_token': str(uuid.uuid4())})
        return self.access_token
    
    def get_portal_url(self, suffix=None, report_type=None, download=None, query_string=None, anchor=None):
        """
            Get a portal url for this model, including access_token.
            The associated route must handle the flags for them to have any effect.
            - suffix: string to append to the url, before the query string
            - report_type: report_type query string, often one of: html, pdf, text
            - download: set the download query string to true
            - query_string: additional query string
            - anchor: string to append after the anchor #
        """
        self.ensure_one()
        url = self.access_url + '%s?access_token=%s%s%s%s%s' % (
            suffix if suffix else '',
            self._portal_ensure_token(),
            '&report_type=%s' % report_type if report_type else '',
            '&download=true' if download else '',
            query_string if query_string else '',
            '#%s' % anchor if anchor else ''
        )
        return url
    
    def convert_tz_utc(self, tz_date):
        fmt = "%Y-%m-%d %H:%M:%S"
        now_utc = datetime.now(timezone('UTC'))
        now_timezone = now_utc.astimezone(timezone(self.env.user.tz))
        UTC_OFFSET_TIMEDELTA = datetime.strptime(now_utc.strftime(fmt), fmt) - datetime.strptime(now_timezone.strftime(fmt), fmt)
        result_utc_datetime = tz_date + UTC_OFFSET_TIMEDELTA
        return result_utc_datetime.strftime(fmt)
    
    @api.model
    def update_timeoff_portal(self, values):
        self = self.sudo()
        user = self.env.user

        response = {}
        try:
            if not (self.env.user.employee_id):
                raise AccessDenied()
            
            if not (values['holiday_status_id'] and values['name']):
                return {
                    'errors': _('All fields are required !')
                }
                
            # Values from Portal Form
            leave_id = values['leave_id']
            name = values['name']
            holiday_status_id = values['holiday_status_id']
            request_date_from = values['request_date_from']
            request_date_to = values['request_date_to']
            request_unit_half = values['request_unit_half']
            request_date_from_period = values['request_date_from_period']
            request_unit_hours = values['request_unit_hours']
            request_hour_from = values['request_hour_from']
            request_hour_to = values['request_hour_to']
            
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)],limit=1)        
            hr_leave_type = self.env['hr.leave.type'].search([('id', '=', holiday_status_id)],limit=1)
            
            date_from = None
            date_to = None

            dt_from = fields.Datetime.from_string(request_date_from)
            dt_to = fields.Datetime.from_string(request_date_to)

            timezone = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
            if dt_from:
                date_from = pytz.utc.localize(dt_from).astimezone(timezone).replace(tzinfo=None)
            if dt_to:
                date_to = pytz.utc.localize(dt_to).astimezone(timezone).replace(tzinfo=None)

            values = {
                'holiday_status_id': int(holiday_status_id),
                'request_date_from':  date_from,
                'request_date_to': date_to,
                'name': name,
                # 'holiday_type' : 'employee',
                'employee_id' : employee.id,
                'request_unit_half': request_unit_half,
                'request_date_from_period': request_date_from_period,
                'request_unit_hours': request_unit_hours,
                'request_hour_from': request_hour_from,
                'request_hour_to': request_hour_to,                
            }
            values.update(self.env['hr.leave'].with_user(employee.user_id)._default_get_request_parameters(values))
            tmp_leave = self.env['hr.leave'].with_user(employee.user_id).new(values)
            tmp_leave._compute_date_from_to()
            values  = tmp_leave._convert_to_write(tmp_leave._cache)
            
            if leave_id:
                leave = self.env['hr.leave'].sudo().browse(int(leave_id))
                leave.write(values)
                response['id'] = leave.id if leave else False
                response['access_token'] = leave.sudo()._portal_ensure_token() if leave else '',

        except (ValidationError, UserError, AccessError, AccessDenied) as e:
            _logger.warning("Validation error: %s", str(e))
            self.env.cr.rollback()
            response["errors"] = str(e)
        
        except Exception as e:
            _logger.exception("Unhandled error during time off creation")
            self.env.cr.rollback()
            response["errors"] = str(e)
        
        return response
            
    
    def _adjust_date_based_on_tz(self, leave_date, hour):
        """ request_date_{from,to} are local to the user's tz but hour_{from,to} are in UTC.

        In some cases they are combined (assuming they are in the same tz) as a datetime. When
        that happens it's possible we need to adjust one of the dates. This function adjust the
        date, so that it can be passed to datetime().

        E.g. a leave in US/Pacific for one day:
        - request_date_from: 1st of Jan
        - request_date_to:   1st of Jan
        - hour_from:         15:00 (7:00 local)
        - hour_to:           03:00 (19:00 local) <-- this happens on the 2nd of Jan in UTC
        """
        user_tz = timezone(self.env.user.tz if self.env.user.tz else 'UTC')
        request_date_to_utc = UTC.localize(datetime.combine(leave_date, hour)).astimezone(user_tz).replace(tzinfo=None)
        return request_date_to_utc.date()
    
    def _get_start_or_end_from_attendance(self, hour, date, employee):
        hour = float_to_time(float(hour))
        holiday_tz = timezone(employee.tz or self.env.user.tz or 'UTC')
        return holiday_tz.localize(datetime.combine(date, hour)).astimezone(UTC).replace(tzinfo=None)
    
    def _default_get_request_parameters(self, values):
        new_values = dict(values)
        if values.get('date_from') and values.get('date_to'):
            date_from = self._adjust_date_based_on_tz(values['date_from'].date(), values['date_from'].time())
            date_to = self._adjust_date_based_on_tz(values['date_to'].date(), values['date_to'].time())
            new_values.update([('request_date_from', date_from), ('request_date_to', date_to)])

            employee = self.env['hr.employee'].browse(values['employee_id']) if values.get('employee_id') else self.env.user.employee_id
            default_start_time = self._get_start_or_end_from_attendance(7, datetime.now().date(), employee).time()
            default_end_time = self._get_start_or_end_from_attendance(19, datetime.now().date(), employee).time()
            if values['date_from'].time() == default_start_time and values['date_to'].time() == default_end_time:
                attendance_from, attendance_to = self._get_attendances(employee, date_from, date_to)
                new_values['date_from'] = self._get_start_or_end_from_attendance(attendance_from.hour_from, date_from, employee)
                new_values['date_to'] = self._get_start_or_end_from_attendance(attendance_to.hour_to, date_to, employee)

        return new_values

    @api.model
    def create_timeoff_portal(self, values):
        self = self.sudo()
        user = self.env.user
        
        response = {}
        try:
            if not user.employee_id:
                raise ValidationError(_('You must be an employee to request time off.'))

            if not (values.get('holiday_status_id') and values.get('name')):
                raise ValidationError(_('All fields are required!'))

            employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            if not employee:
                raise ValidationError(_('Employee record not found.'))

            hr_leave_type = self.env['hr.leave.type'].search([('id', '=', values['holiday_status_id'])], limit=1)
            
            date_from = None
            date_to = None

            dt_from = fields.Datetime.from_string(values['request_date_from'])
            dt_to = fields.Datetime.from_string(values['request_date_to'])

            timezone = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
            if dt_from:
                date_from = pytz.utc.localize(dt_from).astimezone(timezone).replace(tzinfo=None)
            if dt_to:
                date_to = pytz.utc.localize(dt_to).astimezone(timezone).replace(tzinfo=None)

            values = {
                'holiday_status_id': int(values['holiday_status_id']),
                'request_date_from': date_from,
                'request_date_to': date_to,
                'name': values['name'],
                # 'holiday_type': 'employee',
                'employee_id': employee.id,
                'request_unit_half': values['request_unit_half'],
                'request_date_from_period': values['request_date_from_period'],
                'request_unit_hours': values['request_unit_hours'],
                'request_hour_from': values['request_hour_from'],
                'request_hour_to': values['request_hour_to'],
            }

            values.update(self.env['hr.leave'].with_user(employee.user_id)._default_get_request_parameters(values))

            tmp_leave = self.env['hr.leave'].with_user(employee.user_id).new(values)
            tmp_leave._compute_date_from_to()
            values = tmp_leave._convert_to_write(tmp_leave._cache)

            warning = False

            holiday_dates = self._get_public_holiday_dates(
                employee,
                date_from.date(),
                date_to.date()
            )

            if holiday_dates:
                shown_dates = ', '.join(
                    fields.Date.to_string(day)
                    for day in list(holiday_dates)[:5]
                )

                if len(holiday_dates) > 5:
                    shown_dates = '%s, ...' % shown_dates

                warning = {
                    "title": _("Public Holidays Detected"),
                    "message": _(
                        "This request includes %s public holiday day(s): %s. "
                        "These day(s) are excluded from the Time Off duration."
                    ) % (len(holiday_dates), shown_dates)
                }

            leave = self.env['hr.leave'].sudo().create(values)
            if leave:
                response['id'] = leave.id if leave else False
                response['access_token'] = leave.sudo()._portal_ensure_token() if leave else '',

            if warning:
                response['warning'] = warning

        except (ValidationError, UserError, AccessError, AccessDenied) as e:
            _logger.warning("Validation error: %s", str(e))
            self.env.cr.rollback()
            response["errors"] = str(e)
        
        except Exception as e:
            _logger.exception("Unhandled error during time off creation")
            self.env.cr.rollback()
            response["errors"] = str(e)
        return response
    
    @api.model
    def unlink_portal(self, values):
        leave_id = values.get('leave_id')
        if not leave_id:
            return {'success': False, 'error': _('No time off was provided.')}
            
        user = self.env.user
        if not user.employee_id:
            raise AccessDenied()

        if user.has_group('base.group_portal') or user.has_group('base.group_user'):
            leave = self.env['hr.leave'].sudo().browse(int(leave_id))
            
            if not leave.exists():
                return {'success': False, 'error': _('Time off request not found.')}
                
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            if leave.employee_id != employee:
                raise AccessDenied()

            allowed_states = {'confirm', 'validate1', 'cancel'}
            if leave.state not in allowed_states:
                return {
                    'success': False,
                    'error': _('Only time off requests in allowed portal states can be deleted.'),
                }

            try:
                leave.sudo().unlink()
                return {'success': True}
            except Exception as e:
                _logger.error("Error deleting time off %s from portal: %s", leave.id, str(e))
                return {'success': False, 'error': str(e)}
        return {'success': False, 'error': _('You do not have access to delete this time off.')}
