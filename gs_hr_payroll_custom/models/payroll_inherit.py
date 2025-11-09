# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class GsHrPayslipEmployeesInherit(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self):
        for rec in self.employee_ids:
            payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))
            if rec.id and payslip_run.date_start and payslip_run.date_end:
                payslips = self.env['hr.payslip'].search([('employee_id', '=', rec.id)
                                                             ,('date_from', '=', payslip_run.date_start)
                                                             ,('date_to', '=', payslip_run.date_end)
                                                             ,('payment_state', '!=', 'refund')
                                                          ])
                if payslips:
                    raise ValidationError(_('This Employee (' + rec.name + ') ' + 'Already exists'))
        result = super(GsHrPayslipEmployeesInherit, self).compute_sheet()
        return result


class GsHrContractInherit(models.Model):
    _inherit = 'hr.contract'

    struct_id = fields.Many2one('hr.payroll.structure', string="Structure")


class GsAccountMoveInherit(models.Model):
    _inherit = 'account.move'

    gs_payslip_ids = fields.Many2many('hr.payslip', string='Payslip')
    is_true = fields.Boolean(compute="_compute_is_true")

    def _compute_is_true(self):
        for rec in self:
            rec.is_true = False
            if rec.has_reconciled_entries:
                if self.gs_payslip_ids:
                    for payslip in self.gs_payslip_ids:
                        if payslip.payment_state == 'in_payment':
                            payslip.payment_state = 'paid'
                    rec.is_true = True


class GsAccountAccountInherit(models.Model):
    _inherit = 'account.account'

    is_payroll = fields.Boolean()


class GsHrPayslipInherit(models.Model):
    _inherit = 'hr.payslip'

    payment_state = fields.Selection(selection=[
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'paid'),
        ('refund', 'Refund')
    ], string='Payment Status', required=True , default='not_paid')

    gs_account_id = fields.Many2one('account.account', string="Account")
    gs_journal_entries_id = fields.Many2one('account.move', string="Journal Entries")
    is_true = fields.Boolean(compute="_compute_is_true")

    def _cron_state_payroll(self):
        payslips = self.env['hr.payslip'].search([('payment_state', '=', 'in_payment')])
        for payslip in payslips:
            if payslip.gs_journal_entries_id.has_reconciled_entries:
                payslip.payment_state = 'paid'

    def _compute_is_true(self):
        for rec in self:
            rec.is_true = False
            if rec.gs_journal_entries_id.has_reconciled_entries:
                if rec.gs_journal_entries_id.gs_payslip_ids:
                    for payslip in rec.gs_journal_entries_id.gs_payslip_ids:
                        if payslip.payment_state == 'in_payment':
                            payslip.payment_state = 'paid'
                    rec.is_true = True

    @api.onchange('employee_id', 'date_from', 'date_to')
    def unique_payslip(self):
        for rec in self:
            if rec.employee_id and rec.date_from and rec.date_to:
                payslips = self.env['hr.payslip'].search([('employee_id', '=', rec.employee_id.id)
                                                             ,('date_from', '=', rec.date_from)
                                                             ,('date_to', '=', rec.date_to)
                                                             ,('payment_state', '!=', 'refund')
                                                          ])
                if payslips:
                    raise ValidationError(_('This Employee (' + rec.employee_id.name + ') ' + 'Already exists'))

    def refund_sheet(self):
        self.payment_state = 'refund'
        result = super(GsHrPayslipInherit, self).refund_sheet()
        return result

    def _prepare_slip_lines(self, date, line_ids):
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get('Payroll')
        new_lines = []
        for line in self.line_ids.filtered(lambda line: line.category_id):
            amount = -line.total if self.credit_note else line.total
            if line.code == 'NET': # Check if the line is the 'Net Salary'.
                for tmp_line in self.line_ids.filtered(lambda line: line.category_id):
                    if tmp_line.salary_rule_id.not_computed_in_net: # Check if the rule must be computed in the 'Net Salary' or not.
                        if amount > 0:
                            amount -= abs(tmp_line.total)
                        elif amount < 0:
                            amount += abs(tmp_line.total)
            if float_is_zero(amount, precision_digits=precision):
                continue
            debit_account_id = line.salary_rule_id.account_debit.id
            credit_account_id = line.salary_rule_id.account_credit.id

            if debit_account_id: # If the rule has a debit account.
                debit = amount if amount > 0.0 else 0.0
                credit = -amount if amount < 0.0 else 0.0
                debit_line = self._prepare_line_values(line, debit_account_id, date, debit, credit)
                new_lines.append(debit_line)

            if credit_account_id: # If the rule has a credit account.
                debit = -amount if amount < 0.0 else 0.0
                credit = amount if amount > 0.0 else 0.0
                credit_line = self._prepare_line_values(line, credit_account_id, date, debit, credit)
                new_lines.append(credit_line)

        return new_lines

    def create_register_payment(self):
        return {
            'name': _('Register Payment'),
            'res_model': 'register.payment.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': self.env.context,
            'type': 'ir.actions.act_window',
        }

    def _prepare_line_values(self, line, account_id, date, debit, credit):
        slip = line.slip_id
        contract = slip.contract_id
        analytic_distribution = {}

        if debit > 0 and contract:
            for acc in [
                contract.analytic_account_id,
                contract.branch_analytic_account_id,
                contract.department_analytic_account_id
            ]:
                if acc:
                    analytic_distribution[acc.id] = 100.0

        return {
            'name': line.name,
            'partner_id': line.slip_id.employee_id.address_home_id.id,
            'account_id': account_id,
            'journal_id': line.slip_id.struct_id.journal_id.id,
            'date': date,
            'debit': debit,
            'credit': credit,
            'analytic_distribution': analytic_distribution
        }

    # def _prepare_line_values(self, line, account_id, date, debit, credit):
    #     return {
    #         'name': line.name,
    #         'partner_id': line.slip_id.employee_id.address_home_id.id,
    #         'account_id': account_id,
    #         'journal_id': line.slip_id.struct_id.journal_id.id,
    #         'date': date,
    #         'debit': debit,
    #         'credit': credit,
    #         # 'analytic_account_id': line.salary_rule_id.analytic_account_id.id or line.slip_id.contract_id.analytic_account_id.id,
    #     }

    def action_payslip_done(self):
        res = super(GsHrPayslipInherit, self).action_payslip_done()
        for rec in self:
            # if rec.move_id:
            #     rec.move_id.branch_id = rec.employee_id.branch_id.id
            for line in rec.line_ids:
                if line.code == 'NET':
                    if line.total < 0:
                        raise ValidationError(_('Total Salary Less Than Zero'))

        return res