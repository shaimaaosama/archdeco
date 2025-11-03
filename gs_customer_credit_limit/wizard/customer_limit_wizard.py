# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class customer_limit_wizard(models.TransientModel):
    _name = "customer.limit.wizard"
    _description = 'Customer Credit Limit Wizard'

    def set_credit_limit_state(self):
        if self.exceeded_amount >= self.credit_limit:
            raise ValidationError(_('Credit Limit On Hold For This Customer.'))
        order_id = self.env['sale.order'].browse(self._context.get('active_id'))
        order_id.state = 'credit_limit'
        order_id.exceeded_amount = self.exceeded_amount
        order_id.send_mail_approve_credit_limit()
        partner_id = self.partner_id
        if partner_id.parent_id:
            partner_id = partner_id.parent_id
        partner_id.credit_limit_on_hold = self.credit_limit_on_hold
        return True

    def set_credit_limit_state_also_if_has_due(self):
        order_id = self.env['sale.order'].browse(self._context.get('active_id'))
        order_id.state = 'credit_limit'
        order_id.exceeded_amount = self.exceeded_amount
        order_id.send_mail_approve_credit_limit()
        users_g = self.env['res.users'].search(
            [('groups_id', 'in', [self.env.ref('gs_customer_credit_limit.credit_limit_config_on_hold').id])])
        for user in users_g:
            # partner = user.partner_id
            order_id.sudo().make_activity(user.id)
        return True

    current_sale = fields.Float('Current Quotation')
    exceeded_amount = fields.Float('Exceeded Amount')
    credit = fields.Float('Total Receivable')
    partner_id = fields.Many2one('res.partner', string="Customer")
    credit_limit = fields.Float(related='partner_id.credit_limit', string="Credit Limit")
    sale_orders = fields.Char("Sale Orders")
    invoices = fields.Char("Invoices")
    credit_limit_on_hold = fields.Boolean('Credit Limit on Hold')

    t_or_f = fields.Boolean(compute='_compute_t_or_f', store=True)
    order_id = fields.Many2one('sale.order')

    @api.depends('credit_limit', 'current_sale')
    def _compute_t_or_f(self):
        self.t_or_f = False
        t_overdue = 0
        today_date = fields.Date.today()
        if self.order_id.partner_id:
            if self.order_id.partner_id.check_credit:
                search_inv = self.env['account.move'].search([('partner_id', '=', self.order_id.partner_id.id),
                                                              ('payment_state', '!=', 'paid')])
                if search_inv:
                    for m in search_inv:
                        if m.invoice_date_due:
                            if m.invoice_date_due <= today_date:
                                t_overdue += m.amount_residual
                    if t_overdue >= 0.01 and self.order_id.state == 'draft':
                        self.t_or_f = True
                    else:
                        self.t_or_f = False
            return self.t_or_f
