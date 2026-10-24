# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class HrRamadanPeriod(models.Model):
    _name = 'hr.ramadan.period'
    _description = "Ramadan Period"
    _order = 'date_start desc'

    name = fields.Char(required=True, help="e.g. Ramadan 1448")
    date_start = fields.Date("First Day", required=True)
    date_end = fields.Date("Last Day", required=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
        help="Leave empty to apply the period to all companies.")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('date_check', 'CHECK(date_start <= date_end)',
         "The first day of Ramadan must be before its last day."),
    ]

    @api.constrains('date_start', 'date_end', 'company_id', 'active')
    def _check_overlap(self):
        for period in self.filtered('active'):
            domain = [
                ('id', '!=', period.id),
                ('date_start', '<=', period.date_end),
                ('date_end', '>=', period.date_start),
            ]
            if period.company_id:
                domain.append(('company_id', 'in', [False, period.company_id.id]))
            if self.search_count(domain):
                raise ValidationError(_(
                    "The Ramadan period %(name)s overlaps another Ramadan period.",
                    name=period.name))

    def action_recompute_attendance_overtime(self):
        """Recompute attendance overtime of the period, needed when the
        period is created or its dates are corrected after attendances were
        already recorded."""
        if 'hr.attendance' not in self.env:
            raise UserError(_("The Attendances app is not installed."))
        Attendance = self.env['hr.attendance'].sudo()
        for period in self:
            # One extra day on each side covers timezone shifts.
            start = datetime.combine(period.date_start - timedelta(days=1), time.min)
            stop = datetime.combine(period.date_end + timedelta(days=2), time.min)
            domain = [('check_in', '>=', start), ('check_in', '<', stop)]
            if period.company_id:
                domain.append(('employee_id.company_id', '=', period.company_id.id))
            Attendance.search(domain)._update_overtime()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _("Attendance overtime recomputed."),
            },
        }
