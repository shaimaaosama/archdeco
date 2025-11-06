# -*- coding: utf-8 -*-
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError


class GSPaymentApprovalConfig(models.Model):
    _name = 'gs.payment.approval.config'
    _description = 'Payment Approval Configuration'

    name = fields.Char()
    min_amount = fields.Float(string="Minimum Amount", required=True)
    company_ids = fields.Many2many(
        'res.company', string="Allowed Companies", default=lambda self: self.env.company)
    is_boolean = fields.Boolean(string="Employee Always in CC")
    payment_approval_line = fields.One2many(
        'gs.payment.approval.line', 'payment_approval_config_id')
    payment_type_ids = fields.Many2many('gs.payment.type', string='Payment Types ')

    @api.constrains('payment_approval_line')
    def approval_line_level(self):
        if self.payment_approval_line:
            levels = self.payment_approval_line.mapped('level')
            if len(levels) != len(set(levels)):
                raise ValidationError('Levels must be different!!!')
