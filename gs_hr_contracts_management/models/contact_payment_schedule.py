# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GsContactPaymentSchedule(models.Model):
    _name = 'gs.contact.payment.schedule'
    _description = 'Contact Payment Schedule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'contract_barcode_id'

    contract_barcode_id = fields.Many2one('gs.contract.management', string='Contract Barcode', tracking=True, )
    percentage = fields.Float(string="Percentage", tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True)
    contract_classification_id = fields.Many2one('gs.type.of.contracts', string='Contract Classification', related='contract_barcode_id.type_of_contract')

    payment_id = fields.Many2one('gs.payments', string='Payment', tracking=True, )
    book_id = fields.Many2one('gs.subject', string='Book', tracking=True, )

    rate = fields.Float(string="Rate", tracking=True, )

    payment_schedule = fields.Char(string="Notes", tracking=True)
    amount = fields.Float(string="Amount", tracking=True)
    due_date = fields.Date(string="Due Date", tracking=True)
    state = fields.Selection(string='Status',
                              selection=[('draft', 'Draft'),
                                         ('running', 'Running'),
                                         ('expire', 'Expire'),
                                         ('canceled', 'Canceled'),
                                         ], default='draft',
                              required=False, tracking=True)
    status = fields.Selection(string='Payment State',
                              selection=[('paid', 'Paid'),
                                         ('not_paid', 'Not Paid'), ],
                              required=False, default='not_paid', tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', 'contact_payment_attachment_rel', 'contact_payment_template_id',
                                      'contact_payment_attachment_id', 'Attachments', tracking=True, )
    active = fields.Boolean(default=True, tracking=True)

    @api.onchange('contract_barcode_id')
    def _onchange_contract_barcode_id(self):
        for rec in self:
            if rec.contract_barcode_id:
                if not rec.partner_id:
                    rec.partner_id = rec.contract_barcode_id.partner_id

    @api.onchange('payment_id')
    def _onchange_payment_id(self):
        for rec in self:
            if rec.payment_id:
                rec.percentage = rec.payment_id.percentage

    @api.onchange('percentage')
    def _onchange_payment_id(self):
        for rec in self:
            if rec.percentage:
                rec.amount = (rec.percentage / 100) * rec.contract_barcode_id.amount