# models/register_general_payment_wizard.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RegisterGeneralPaymentWizard(models.TransientModel):
    _name = 'register.general.payment.wizard'
    _description = 'General Payment Registration Wizard'

    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        domain="[('type', 'in', ('bank', 'cash'))]",
        required=True
    )
    account_id = fields.Many2one(
        'account.account',
        string='Account to Debit',
        required=True
    )
    amount = fields.Monetary(string='Amount', required=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    payment_date = fields.Date(string='Date', default=fields.Date.context_today)
    memo = fields.Char(string='Memo')

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.journal_id:
            self.currency_id = self.journal_id.currency_id or self.env.company.currency_id

    def action_create_payment_entry(self):
        if self.amount <= 0:
            raise UserError(_("Amount must be greater than 0."))

        move_vals = {
            'journal_id': self.journal_id.id,
            'date': self.payment_date,
            'ref': self.memo or 'Manual Payment',
            'line_ids': [
                (0, 0, {
                    'account_id': self.account_id.id,
                    'debit': self.amount,
                    'credit': 0.0,
                    'name': self.memo or '/',
                }),
                (0, 0, {
                    'account_id': self.journal_id.outbound_payment_method_line_ids.payment_account_id.id,
                    'debit': 0.0,
                    'credit': self.amount,
                    'name': self.memo or '/',
                }),
            ],
        }

        move = self.env['account.move'].create(move_vals)
        active_ids = self.env.context.get('active_ids', [])
        records = self.env['gs.penalties.awards'].browse(active_ids)

        for rec in records:
            rec.journal_entry_id = move.id
            rec.action_paid()
        move.action_post()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': move.id,
            'target': 'current',
        }
