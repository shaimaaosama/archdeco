from odoo import models,fields,api


class penaltyCash(models.TransientModel):
    _name = "penalty.cash"
    _description = "Penalty Cash Payment Wizard"

    journal_id = fields.Many2one('account.journal',  check_company=False,
        domain="[('type', 'in', ['cash', 'bank'])]")
    pa_installment_loan_id = fields.Many2one('gs.penalties.awards.installment', string='Penalty Installment')
    pa_installment_loan_ids = fields.Many2many('gs.penalties.awards.installment', string='Penalty Installments', compute='_compute_installment')
    amount = fields.Float('Amount')
    account_id = fields.Many2one('account.account', domain=[('deprecated', '=', False)])

    @api.onchange('pa_installment_loan_id')
    def _onchange_pa_installment_loan_id(self):
        if self.pa_installment_loan_id:
            self.amount = self.pa_installment_loan_id.installment_amt

    @api.depends('journal_id')
    def _compute_installment(self):
        for record in self:
            active_id = self.env.context.get('active_id')
            loan = self.env['gs.penalties.awards'].browse(active_id)
            if loan:
                record.pa_installment_loan_ids = loan.pa_installment_ids.filtered(lambda x:not x.is_paid)
            else:
                record.pa_installment_loan_ids = False

    @api.onchange('journal_id', 'pa_installment_loan_ids')
    def _onchange_available_installments(self):
        allowed_ids = self.pa_installment_loan_ids.ids
        if self.pa_installment_loan_id and self.pa_installment_loan_id.id not in allowed_ids:
            self.pa_installment_loan_id = False
            self.amount = 0.0
        return {'domain': {'pa_installment_loan_id': [('id', 'in', allowed_ids)]}}

    def payment(self):
        active_id = self.env.context.get('active_id')
        loan = self.env['gs.penalties.awards'].browse(active_id)
        contract = self.env['hr.contract'].search([('employee_id', '=', loan.employee_id.id),('state', '=', 'open')])

        if loan:
            debit_vals = {
                'name': self.pa_installment_loan_id.name,
                'account_id': self.journal_id.default_account_id.id,
                'debit': self.amount,
                'credit': 0.0,
                'partner_id': loan.employee_id.address_home_id.id,
                'analytic_distribution': {contract.analytic_account_id.id: 100} if contract else False,
            }

            credit_vals = {
                'name':  self.pa_installment_loan_id.name,
                'account_id': self.account_id.id,
                'debit':  0.0,
                'credit': self.amount,
                'partner_id': loan.employee_id.address_home_id.id,
                'analytic_distribution': {contract.analytic_account_id.id: 100} if contract else False,

            }
            vals = {
                'name': 'Payment Penalty' + ' ' + self.pa_installment_loan_id.name,
                'ref': self.pa_installment_loan_id.name,
                'journal_id': self.journal_id.id,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
                'move_type': 'entry',
                'pa_installment_loan_id': self.pa_installment_loan_id.id,
            }

            move = self.env['account.move'].create(vals)
            move.action_post()



