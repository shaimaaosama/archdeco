# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GSAccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_order_id = fields.Many2one('gs.payment.order',)
    is_posted = fields.Boolean(compute='_compute_is_posted')

    def _compute_is_posted(self):
        for rec in self:
            rec.is_posted = False
            if rec.payment_order_id:
                payment = self.env['account.payment'].search([('payment_order_id', '=', rec.payment_order_id.id)])
                amount = 0
                for pay in payment:
                    if pay.state == 'posted':
                        amount += pay.amount
                        rec.is_posted = True
                # if rec.is_posted and amount == rec.payment_order_id.amount:
                #     rec.payment_order_id.state = 'close'