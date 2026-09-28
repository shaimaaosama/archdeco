# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

from ..exceptions import MobileApiError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    mobile_app_access = fields.Boolean(
        string='Mobile App Access', default=True, groups='hr.group_hr_user', copy=False,
        help="Allow this employee to sign in to the mobile app with their work email and PIN.")
    mobile_attendance_restriction = fields.Selection([
        ('work_location', 'Work Location'),
        ('company', 'Company'),
        ('none', 'None'),
    ], string='Mobile Attendance Location', default='work_location', required=True,
        groups='hr.group_hr_user', copy=False,
        help="Where the employee is required to be, GPS-wise, to check in/out from the "
             "mobile app:\n"
             "- Work Location: within the radius configured on their work location.\n"
             "- Company: within the radius configured on the company.\n"
             "- None: no geofence check (e.g. drivers, field staff).")
    mobile_failed_attempts = fields.Integer(
        string='Mobile Failed Login Attempts', default=0, groups='hr.group_hr_user', copy=False)
    mobile_locked_until = fields.Datetime(
        string='Mobile Login Locked Until', groups='hr.group_hr_user', copy=False)
    mobile_token_ids = fields.One2many(
        'hr.employee.mobile.token', 'employee_id', string='Mobile App Sessions',
        groups='hr.group_hr_user', copy=False)
    mobile_active_token_count = fields.Integer(
        string='Active Mobile Sessions', compute='_compute_mobile_active_token_count',
        groups='hr.group_hr_user')

    @api.depends('mobile_token_ids.active')
    def _compute_mobile_active_token_count(self):
        for employee in self:
            employee.mobile_active_token_count = len(
                employee.mobile_token_ids.filtered('active'))

    def _mobile_get_geofence(self):
        """Return ``{mode, name, latitude, longitude, radius}`` for this employee's
        mobile attendance geofence, or ``None`` when their restriction mode is ``none``.

        Raises ``MobileApiError('LOCATION_NOT_CONFIGURED', 409, ...)`` when the
        applicable work location/company has no coordinates or a radius <= 0.
        Never silently falls back from work location to company.
        """
        self.ensure_one()
        mode = self.mobile_attendance_restriction

        if mode == 'work_location':
            location = self.work_location_id
            if not location or (not location.attendance_latitude and not location.attendance_longitude) \
                    or location.attendance_radius <= 0:
                raise MobileApiError(
                    'LOCATION_NOT_CONFIGURED', 409,
                    _("Your work location has no GPS coordinates configured. Contact HR."))
            return {
                'mode': 'work_location',
                'name': location.name,
                'latitude': location.attendance_latitude,
                'longitude': location.attendance_longitude,
                'radius': location.attendance_radius,
            }

        if mode == 'company':
            company = self.company_id
            if (not company.attendance_latitude and not company.attendance_longitude) \
                    or company.attendance_radius <= 0:
                raise MobileApiError(
                    'LOCATION_NOT_CONFIGURED', 409,
                    _("Your company has no GPS coordinates configured. Contact HR."))
            return {
                'mode': 'company',
                'name': company.name,
                'latitude': company.attendance_latitude,
                'longitude': company.attendance_longitude,
                'radius': company.attendance_radius,
            }

        # mode == 'none'
        return None

    def action_mobile_revoke_sessions(self):
        """Deactivate every active mobile app session token for these employees."""
        self.mapped('mobile_token_ids').filtered('active').write({'active': False})

    def action_mobile_unlock(self):
        """Reset the mobile login lockout for these employees."""
        self.write({'mobile_failed_attempts': 0, 'mobile_locked_until': False})

    def write(self, vals):
        keep_token_ids = set(self.env.context.get('mobile_keep_token_ids') or [])
        # Only a PIN change, Mobile App Access being turned OFF, or the employee
        # being archived should revoke sessions. Turning access back ON (or any
        # other field change) must not touch existing sessions.
        should_revoke = (
            'pin' in vals
            or vals.get('mobile_app_access') is False
            or vals.get('active') is False
        )
        res = super().write(vals)
        if should_revoke:
            for employee in self:
                # sudo(): a user without hr.group_hr_user (mobile_token_ids and
                # the token model are both restricted to that group) can still
                # legitimately change their own pin/active here, e.g. through
                # another flow; do not let that raise an AccessError.
                tokens = employee.sudo().mobile_token_ids.filtered('active')
                if keep_token_ids:
                    tokens = tokens.filtered(lambda t: t.id not in keep_token_ids)
                if tokens:
                    tokens.write({'active': False})
        return res
