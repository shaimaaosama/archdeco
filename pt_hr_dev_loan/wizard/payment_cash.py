from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class PaymentCash(models.TransientModel):
    _name = "payment.cash"
    _description = "Loan Cash Payment Wizard"

    journal_id = fields.Many2one(
        'account.journal',
        check_company=False,
        domain="[('type', 'in', ['cash', 'bank'])]",
        required=True
    )
    installment_loan_ids = fields.Many2many(
        'installment.line',
        string='Installment Lines',
        compute='_compute_installment',
        store=False
    )
    selected_installment_ids = fields.Many2many(
        'installment.line',
        string='Selected Installments',
        domain="[('id', 'in', installment_loan_ids)]"
    )
    amount = fields.Float('Total Amount', compute='_compute_amount', store=False)

    @api.depends('selected_installment_ids')
    def _compute_amount(self):
        for record in self:
            record.amount = sum(line.installment_amt for line in record.selected_installment_ids)

    @api.depends('journal_id')
    def _compute_installment(self):
        for record in self:
            active_id = self.env.context.get('active_id')
            loan = self.env['employee.loan'].browse(active_id)
            if loan:
                record.installment_loan_ids = loan.installment_lines.filtered(lambda x: not x.is_paid)
            else:
                record.installment_loan_ids = False

    def payment(self):
        _logger.info("Processing multi-line payment")

        active_id = self.env.context.get('active_id')
        loan = self.env['employee.loan'].browse(active_id)
        if not loan:
            raise UserError(_("No loan found."))

        if not self.selected_installment_ids:
            raise UserError(_("No installment lines selected."))

        contract = self.env['hr.contract'].search([
            ('employee_id', '=', loan.employee_id.id),
            ('state', '=', 'open')
        ], limit=1)

        total_amount = sum(line.installment_amt for line in self.selected_installment_ids)

        debit_vals = {
            'name': 'Loan Payment',
            'account_id': loan.loan_type_id.loan_account.id,
            'debit': 0.0,
            'credit': total_amount,
            'partner_id': loan.employee_id.address_home_id.id,
            'analytic_distribution': {contract.analytic_account_id.id: 100} if contract else False,
        }

        credit_vals = {
            'name': 'Loan Payment',
            'account_id': self.journal_id.inbound_payment_method_line_ids.payment_account_id.id,
            'debit': total_amount,
            'credit': 0.0,
            'partner_id': loan.employee_id.address_home_id.id,
            'analytic_distribution': {contract.analytic_account_id.id: 100} if contract else False,
        }
        installment_names = ', '.join(self.selected_installment_ids.mapped('name'))

        move = self.env['account.move'].create({
            'ref': ', '.join(self.selected_installment_ids.mapped('name')),
            'journal_id': self.journal_id.id,
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
            'move_type': 'entry',
        })
        move.action_post()

        # Link move to each selected installment and mark as paid
        for line in self.selected_installment_ids:
            line.write({
                'is_paid': True,
                'journal_entry_id': move.id
            })

        # Show the created move
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': move.id,
            'target': 'current',
        }



