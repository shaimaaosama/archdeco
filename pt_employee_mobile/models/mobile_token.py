# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models


class HrEmployeeMobileToken(models.Model):
    _name = 'hr.employee.mobile.token'
    _description = 'Employee Mobile App Session Token'
    _order = 'create_date desc'
    _rec_name = 'device_name'

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, ondelete='cascade', index=True)
    token_hash = fields.Char(string='Token Hash', required=True, index=True, copy=False)
    device_id = fields.Char(string='Device ID')
    device_name = fields.Char(string='Device Name')
    platform = fields.Char(string='Platform')
    app_version = fields.Char(string='App Version')
    last_used = fields.Datetime(string='Last Used')
    expires_at = fields.Datetime(string='Expires At', required=True, index=True)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('token_hash_unique', 'unique(token_hash)', 'This mobile session token already exists.'),
    ]

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
