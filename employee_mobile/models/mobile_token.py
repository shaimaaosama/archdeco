# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models

# Prefixes the app puts in front of a real, per-device unique identifier
# (Android ANDROID_ID, iOS identifierForVendor, a random per-browser/per-install
# UUID). Older app builds sent the Android *build* id, which is shared by every
# phone of the same model/firmware, so un-prefixed ids are never compared
# across employees.
TRUSTED_DEVICE_ID_PREFIXES = ('android:', 'ios:', 'web:', 'install:')


def is_trusted_device_id(device_id):
    return bool(device_id) and device_id.startswith(TRUSTED_DEVICE_ID_PREFIXES)


class HrEmployeeMobileToken(models.Model):
    _name = 'hr.employee.mobile.token'
    _description = 'Employee Mobile App Session Token'
    _order = 'create_date desc'
    _rec_name = 'device_name'

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, ondelete='cascade', index=True)
    token_hash = fields.Char(string='Token Hash', required=True, index=True, copy=False)
    device_id = fields.Char(string='Device ID', index=True,
                            help="Unique identifier of the phone/browser the employee signed in from.")
    device_name = fields.Char(string='Device Name')
    platform = fields.Char(string='Platform')
    app_version = fields.Char(string='App Version')
    last_used = fields.Datetime(string='Last Used')
    expires_at = fields.Datetime(string='Expires At', required=True, index=True)
    active = fields.Boolean(string='Active', default=True)

    device_shared_employee_ids = fields.Many2many(
        'hr.employee', string='Device Also Used By', compute='_compute_device_shared_employee_ids',
        help="Other employees who signed in or punched attendance from this same device.")
    device_shared = fields.Boolean(
        string='Shared Device', compute='_compute_device_shared_employee_ids',
        search='_search_device_shared')

    _sql_constraints = [
        ('token_hash_unique', 'unique(token_hash)', 'This mobile session token already exists.'),
    ]

    @api.model
    def _get_device_employees(self, device_id):
        """All employees that ever used ``device_id`` (sessions, including revoked
        ones, and mobile attendances). Empty for untrusted/legacy ids."""
        Employee = self.env['hr.employee'].sudo()
        if not is_trusted_device_id(device_id):
            return Employee
        tokens = self.sudo().with_context(active_test=False).search([('device_id', '=', device_id)])
        attendances = self.env['hr.attendance'].sudo().search([
            '|', ('mobile_check_in_device_id', '=', device_id),
            ('mobile_check_out_device_id', '=', device_id),
        ])
        return tokens.employee_id | attendances.employee_id

    @api.depends('device_id', 'employee_id')
    def _compute_device_shared_employee_ids(self):
        cache = {}
        for token in self:
            if token.device_id not in cache:
                cache[token.device_id] = self._get_device_employees(token.device_id)
            others = cache[token.device_id] - token.employee_id
            token.device_shared_employee_ids = others
            token.device_shared = bool(others)

    def _search_device_shared(self, operator, value):
        if operator not in ('=', '!=') or not isinstance(value, bool):
            raise NotImplementedError(operator, value)
        self.env['hr.employee.mobile.token'].flush_model(['device_id', 'employee_id'])
        self.env.cr.execute("""
            SELECT device_id FROM hr_employee_mobile_token
             WHERE device_id LIKE ANY(%s)
          GROUP BY device_id
            HAVING COUNT(DISTINCT employee_id) > 1
        """, ([p + '%' for p in TRUSTED_DEVICE_ID_PREFIXES],))
        shared_ids = [row[0] for row in self.env.cr.fetchall()]
        positive = (operator == '=') == value
        return [('device_id', 'in' if positive else 'not in', shared_ids)]

    @api.model
    def _cron_cleanup_tokens(self):
        """Delete expired tokens, and inactive (revoked) tokens older than 30 days."""
        now = fields.Datetime.now()
        cutoff = now - timedelta(days=30)
        domain = [
            '|',
            ('expires_at', '<', now),
            '&', ('active', '=', False), ('write_date', '<', cutoff),
        ]
        self.sudo().with_context(active_test=False).search(domain).unlink()
