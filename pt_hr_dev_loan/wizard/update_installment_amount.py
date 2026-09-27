# -*- coding: utf-8 -*-

from odoo import models,api, fields, _
from odoo.exceptions import ValidationError


class UpdateInstallmentAmount(models.TransientModel):
    _name = "gs.update.installment.amount"
    _description = "Loan Installment Update Wizard"

    employee_loan_id = fields.Many2one('employee.loan')
    installment_line_ids = fields.Many2many('installment.line')

    installment_line_from_id = fields.Many2one('installment.line', string='From',)
    installment_line_from_ids = fields.Many2many('installment.line','installment_lines01','installment_lines001','installment_lines0001', string='From Installments',)
    installment_amt_now = fields.Float('Installment Amt')
    amount = fields.Float('New Amount')

    installment_line_to_id = fields.Many2one('installment.line', string='To',)
    installment_amt_to = fields.Float()
    amount_update = fields.Float()
    type = fields.Selection(
        string='Type',
        selection=[('current_installment', 'Current Installment '),
                   ('new_installment', 'New Installment')], default='current_installment')
    date_to = fields.Date(string='Date To')

    @api.onchange('employee_loan_id')
    def onchange_installment_line_ids(self):
        for rec in self:
            if rec.employee_loan_id:
                for lin in rec.employee_loan_id.installment_lines:
                    if not lin.is_paid:
                        if not lin.is_skip:
                            rec.installment_line_ids = [(4, lin.id)]

    @api.onchange('installment_line_from_ids','installment_amt_now', 'amount')
    def onchange_installment_amt_now(self):
        for rec in self:
            installment_amt = 0
            if rec.installment_line_from_ids:
                for line in rec.installment_line_from_ids:
                    installment_amt += line.installment_amt

                rec.installment_amt_now = installment_amt
                if rec.amount > rec.installment_amt_now:
                    raise ValidationError(_('New Amount Bigger Than Installment Amount %s', rec.installment_amt_now))
                else:
                    rec.amount_update = rec.installment_amt_now - rec.amount

    @api.onchange('installment_line_to_id')
    def onchange_installment_amt_to(self):
        for rec in self:
            if rec.installment_line_to_id:
                rec.installment_amt_to = rec.installment_line_to_id.installment_amt

    # def action_update_installment_amount(self):
    #     for rec in self:
    #         if rec.type == 'current_installment':
    #             for line in rec.installment_line_from_ids:
    #                 line.installment_amt = rec.amount
    #             rec.installment_line_to_id.installment_amt = rec.installment_amt_to + rec.amount_update
    #         elif rec.type == 'new_installment':
    #             for line in rec.installment_line_from_ids:
    #                 line.installment_amt = rec.amount
    #             vals = {
    #                 'loan_id': rec.employee_loan_id.id,
    #                 'employee_id': rec.employee_loan_id.employee_id.id,  # <== Add this line
    #                 'name': 'INS - ' + rec.employee_loan_id.name + ' - ' + str(len(rec.installment_line_ids) + 1),
    #                 'date': rec.date_to,
    #                 'installment_amt': rec.amount_update,
    #             }
    #             self.env['installment.line'].create(vals)

    def action_update_installment_amount(self):
        for rec in self:
            if rec.type == 'current_installment':
                # Update the current installments
                for line in rec.installment_line_from_ids:
                    line.installment_amt = rec.amount
                rec.installment_line_to_id.installment_amt = rec.installment_amt_to + rec.amount_update

            elif rec.type == 'new_installment':
                # Update the selected installments with the new amount
                for line in rec.installment_line_from_ids:
                    line.installment_amt = rec.amount

                # Generate a unique name for the new installment
                base_name = f'INS - {rec.employee_loan_id.name} - '
                number = 1
                existing_names = rec.employee_loan_id.installment_lines.mapped('name')
                while f'{base_name}{number}' in existing_names:
                    number += 1
                new_name = f'{base_name}{number}'

                # Create the new installment line with the updated amount
                vals = {
                    'loan_id': rec.employee_loan_id.id,
                    'name': new_name,
                    'date': rec.date_to,
                    'installment_amt': rec.amount_update,
                }
                self.env['installment.line'].create(vals)
