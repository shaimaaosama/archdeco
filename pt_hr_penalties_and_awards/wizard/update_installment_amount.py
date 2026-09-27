# -*- coding: utf-8 -*-

from odoo import models,api, fields, _
from odoo.exceptions import ValidationError


class UpdateInstallmentAmount(models.TransientModel):
    _name = "gs.pa.update.amount"
    _description = "Penalties And Awards Installment Update Wizard"

    penalties_awards_id = fields.Many2one('gs.penalties.awards')
    installment_line_ids = fields.Many2many('gs.penalties.awards.installment')
    installment_line_from_id = fields.Many2one('gs.penalties.awards.installment', string='From',)
    installment_amt_now = fields.Float('Installment Amt')
    amount = fields.Float('New Amount')

    installment_line_to_id = fields.Many2one('gs.penalties.awards.installment', string='To',)
    installment_amt_to = fields.Float()
    amount_update = fields.Float()
    type = fields.Selection(
        string='Type',
        selection=[('current_installment', 'Current Installment '),
                   ('new_installment', 'New Installment')], default='current_installment')
    date_to = fields.Date(string='Date To')

    @api.onchange('penalties_awards_id')
    def onchange_installment_line_ids(self):
        for rec in self:
            if rec.penalties_awards_id:
                for lin in rec.penalties_awards_id.pa_installment_ids:
                    if not lin.is_paid:
                        if not lin.is_skip:
                            rec.installment_line_ids = [(4, lin.id)]

    @api.onchange('installment_line_from_id','installment_amt_now', 'amount')
    def onchange_installment_amt_now(self):
        for rec in self:
            if rec.installment_line_from_id:
                rec.installment_amt_now = rec.installment_line_from_id.installment_amt
                if rec.amount > rec.installment_amt_now:
                    raise ValidationError(_('New Amount Bigger Than Installment Amount %s', rec.installment_amt_now))
                else:
                    rec.amount_update = rec.installment_amt_now - rec.amount

    @api.onchange('installment_line_to_id')
    def onchange_installment_amt_to(self):
        for rec in self:
            if rec.installment_line_to_id:
                rec.installment_amt_to = rec.installment_line_to_id.installment_amt

    def action_update_installment_amount(self):
        for rec in self:
            if rec.type == 'current_installment':
                for line in rec.installment_line_from_id:
                    line.installment_amt = rec.amount
                rec.installment_line_to_id.installment_amt = rec.installment_amt_to + rec.amount_update
            elif rec.type == 'new_installment':
                for line in rec.installment_line_from_id:
                    line.installment_amt = rec.amount
                vals = {
                    'penalties_awards_id': rec.penalties_awards_id.id,
                    'name': 'INS - ' + rec.penalties_awards_id.display_name + ' - ' + str(len(rec.installment_line_ids) + 1),
                    'date': rec.date_to,
                    'installment_amt': rec.amount_update,
                }
                self.env['gs.penalties.awards.installment'].create(vals)