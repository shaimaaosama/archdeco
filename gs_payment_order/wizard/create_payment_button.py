# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CreatePaymentWizard(models.TransientModel):
    _name = 'gs.create.payment.wizard'

    amount = fields.Float(string='Amount')
    journal_id = fields.Many2one('account.journal', string='Payment Journal', domain=[('type', 'in', ['bank', 'cash'])])
    currency_id = fields.Many2one('res.currency', string='Currency',)

    def create_payment_wizard(self):
        active_id = self._context.get('active_ids') or self._context.get('active_id')
        payment_order = self.env['gs.payment.order'].search([('id', '=', active_id)])
        if self.amount > payment_order.amount_payment_available:
            raise ValidationError(
                _('Attention !! your amount bigger than available amount , available amount is (%s)' % (payment_order.amount_payment_available)))
        payment_order.action_create_payment(self.amount, self.journal_id, self.currency_id)