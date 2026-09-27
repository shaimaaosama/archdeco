from odoo import api, fields, models


class HRLeaveInherit(models.Model):
    _inherit = 'hr.leave'

    number_of_days_display = fields.Float(
        'Duration in Days', compute='_compute_number_of_days_display_new', readonly=True,
        help='Number of days of the time off request according to your working schedule. Used for interface.')

    number_of_days = fields.Float(
        'Duration (Days)', compute='_compute_number_of_days_new', store=True, readonly=False, copy=False,
        tracking=True,
        help='Number of days of the time off request. Used in the calculation. To manually correct the duration, use this field.')

    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_number_of_days_display_new(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                wd_diff = fields.Datetime.from_string(rec.date_to) - fields.Datetime.from_string(rec.date_from)
                rec.number_of_days_display = wd_diff.days + 1
            else:
                rec.number_of_days_display = 0.0

    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_number_of_days_new(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                wd_diff = fields.Datetime.from_string(rec.date_to) - fields.Datetime.from_string(rec.date_from)
                rec.number_of_days = wd_diff.days + 1
            else:
                rec.number_of_days = 0.0

    # @api.constrains('request_date_from', 'request_date_to')
    # def _check_expiration_date(self):
    #     for rec in self:
    #         list_employees = {}
    #         for emp in rec.employee_ids:
    #             if (rec.request_date_from and emp.id_expiry_date_new and rec.request_date_from > emp.id_expiry_date_new) or (rec.request_date_to and emp.id_expiry_date_new and rec.request_date_to > emp.id_expiry_date_new):
    #                 list_employees[emp.name] = emp.id_expiry_date_new.strftime('%Y-%m-%d')
    #         if list_employees:
    #             raise UserError(_(f'those employees are expiry date identification ID {list_employees}.'))
