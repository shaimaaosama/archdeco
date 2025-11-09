# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from odoo import models, fields, api, exceptions, _
import math
import logging

_logger = logging.getLogger(__name__)


class Settlement(models.TransientModel):
    _name = 'hr.benefit.settlement'

    def _default_debit_account_id(self):
        return self.env.user.company_id.debit_account_id

    def _default_expense_account_id(self):
        return self.env.user.company_id.expense_account_id

    def _default_expense_journal_id(self):
        return self.env.user.company_id.expense_journal_id

    def _default_settlement_journal_id(self):
        return self.env.user.company_id.settlement_journal_id

    request_id = fields.Many2one(comodel_name="hr.end.service.benefit")
    employee_id = fields.Many2one(comodel_name="hr.employee", related='request_id.employee_id')
    amount = fields.Float(related='request_id.amount')
    total_payslip_deserved_amount = fields.Float(related='request_id.total_payslip_deserved_amount')
    settlement_journal_id = fields.Many2one(comodel_name="account.journal", default=_default_settlement_journal_id)
    payment_date = fields.Date(string=" Payment Date", default=datetime.now().strftime('%Y-%m-%d'), )
    expense_account_id = fields.Many2one(comodel_name="account.account", default=_default_expense_account_id)
    expense_journal_id = fields.Many2one(comodel_name="account.journal", default=_default_expense_journal_id, )
    expense_date = fields.Date(string="Expense Date", default=datetime.now().strftime('%Y-%m-%d'), )

    # def settle_employee_reward(self):
    #     for record in self:
    #         if not record.employee_id.address_home_id:
    #             raise exceptions.ValidationError(
    #                 _("This employee has no private address,"
    #                   " please add it at employee profile !!"))
    #         # if not record.employee_id.address_home_id:
    #         #     raise exceptions.ValidationError(
    #         #         _("This employee private address is not a supplier, please mark it as a supplier!!"))
    #         if not record.employee_id.address_home_id.property_account_payable_id:
    #             raise exceptions.ValidationError(
    #                 _("This employee has no payable account at private address,"
    #                   " please add it at employee private address partner !!"))
    #         # Journal Entry Creation
    #         line_ids = []
    #         name = _('Ending service reward settlement of %s') % (record.employee_id.name)
    #         move_dict = {
    #             'narration': name,
    #             'ref': name,
    #             'journal_id': record.expense_journal_id.id,
    #             'date': record.expense_date,
    #         }
    #         amount = record.amount
    #         total_payslip_deserved_amount = record.total_payslip_deserved_amount
    #         debit_account_id = record.expense_account_id.id
    #         credit_account_id = record.employee_id.address_home_id.property_account_payable_id.id
    #         if debit_account_id and record.employee_id.address_home_id:
    #             debit_line = (0, 0, {
    #                 'name': name + str(' debit line'),
    #                 'partner_id': record.employee_id.address_home_id.id,
    #                 'account_id': debit_account_id,
    #                 'journal_id': record.expense_journal_id.id,
    #                 'date': record.expense_date,
    #                 'debit': amount > 0.0 and amount or 0.0,
    #                 'credit': amount < 0.0 and -amount or 0.0,
    #             })
    #             line_ids.append(debit_line)
    #         if credit_account_id:
    #             credit_line = (0, 0, {
    #                 'name': name + str(' credit line'),
    #                 'partner_id': record.employee_id.address_home_id.id,
    #                 'account_id': credit_account_id,
    #                 'journal_id': record.expense_journal_id.id,
    #                 'date': record.expense_date,
    #                 'debit': amount < 0.0 and -amount or 0.0,
    #                 'credit': amount > 0.0 and amount or 0.0,
    #             })
    #             line_ids.append(credit_line)
    #         move_dict['line_ids'] = line_ids
    #         move = self.env['account.move'].with_context(check_move_validity=False).create([move_dict])
    #         move.action_post()
    #
    #         # Payment Creation
    #         name = _('Ending service reward payment of %s') % (record.employee_id.name)
    #         payment_dict = {
    #             # 'communication': name,
    #             'reward_id': record.request_id.id,
    #             'payment_type': 'outbound',
    #             'partner_type': 'supplier',
    #             'amount': record.amount,
    #             'journal_id': record.settlement_journal_id.id,
    #             'partner_id': record.employee_id.address_home_id.id,
    #             # 'payment_method_line_id': record.settlement_journal_id.outbound_payment_method_line_ids[0].id,
    #             'date': record.payment_date,
    #         }
    #         payment_id = self.env['account.payment'].create(payment_dict)
    #         payment_id.action_post()
    #         if record.total_payslip_deserved_amount > 0:
    #             # payslip_name = _('Ending service payslip payment of %s') % (record.employee_id.name)
    #             # payslip_payment_dict = {
    #             #     # 'communication': name,
    #             #     'reward_id': record.request_id.id,
    #             #     'payment_type': 'outbound',
    #             #     'partner_type': 'supplier',
    #             #     'amount': record.total_payslip_deserved_amount,
    #             #     'journal_id': record.settlement_journal_id.id,
    #             #     'partner_id': record.employee_id.address_home_id.id,
    #             #     'payment_method_line_id': record.settlement_journal_id.outbound_payment_method_line_ids[0].id,
    #             #     'date': record.payment_date,
    #             # }
    #             # payslip_payment_id = self.env['account.payment'].create(payslip_payment_dict)
    #             # payslip_payment_id.action_post()
    #             # record.request_id.write(
    #             #     {'account_move_id': move.id, 'payment_id': payment_id.id,
    #             #      'payslip_payment_id': payslip_payment_id.id, 'state': 'paid'})
    #             pass
    #         else:
    #             record.request_id.write(
    #                 {'account_move_id': move.id, 'payment_id': payment_id.id, 'state': 'paid'})
    def settle_employee_reward_emp(self):
        """Function to create a balanced account.move (journal entry) for the settlement."""
        for record in self:
            line_ids = []
            # /////////////////////////////////////////////////////////////////////////
            # 🔹 Credit line (Ending Service Reward Settlement)
            journal = record.expense_journal_id
            credit_account_id = False

            # ✅ Choose account based on journal type
            if journal:
                if journal.type == 'general' and journal.gs_def_credit_acc:
                    credit_account_id = journal.gs_def_credit_acc.id
                elif journal.type == 'purchase' and journal.default_account_id:
                    credit_account_id = journal.default_account_id.id
                elif journal.default_account_id:
                    credit_account_id = journal.default_account_id.id
                else:
                    credit_account_id = record.employee_id.address_home_id.property_account_payable_id.id

            if not credit_account_id:
                raise exceptions.ValidationError(_(
                    "No valid credit account found! Please configure 'Default Credit Account' "
                    "in the Expense Journal or set a Payable Account on the employee’s partner."
                ))

            credit_line = (0, 0, {
                'name': _('Ending Service Reward Settlement (Credit) for %s') % record.employee_id.name,
                'partner_id': record.employee_id.address_home_id.id,
                'account_id': credit_account_id,  # ✅ from gs_def_credit_acc or default_account_id
                'journal_id': journal.id,
                'date': record.expense_date,
                'debit': 0.0,
                'credit': record.amount,
            })
            line_ids.append(credit_line)
            # ///////////////////////////////////////////////////
            account_holiday = self.env["type.allowances"].search([('type', '=', 'holidays')], limit=1)
            if account_holiday:
                if account_holiday.is_type_collected:
                    ac_holiday = account_holiday.line_ids[0].account_type_allowances_id.id
                else:
                    ac_holiday = account_holiday.account.id
                if not ac_holiday:
                    raise exceptions.ValidationError(
                        _("Enter the account in Holiday Allowance Type"))
                debit_line_2 = (0, 0, {
                    'name': "Total Time Off Deserved Amount",
                    'partner_id': record.employee_id.address_home_id.id,
                    'account_id': ac_holiday,
                    'journal_id': record.expense_journal_id.id,
                    'date': record.expense_date,
                    'debit': record.request_id.total_holiday_deserved_amount > 0.0 and record.request_id.total_holiday_deserved_amount or 0.0,
                    'credit': record.request_id.total_holiday_deserved_amount < 0.0 and -record.request_id.total_holiday_deserved_amount or 0.0,
                })
                line_ids.append(debit_line_2)

            account_payroll = self.env["type.allowances"].search([('type', '=', 'payroll')], limit=1)
            if not account_payroll or not account_payroll.line_ids:
                raise exceptions.ValidationError(
                    _("No payroll account lines configured. Please check the 'type.allowances' settings for payroll."))
            payroll_account = []
            for allowances in account_payroll.line_ids:
                if allowances.structure_id.id == record.employee_id.contract_id.struct_id.id:
                    payroll_account = allowances.account_type_allowances_id.id
                    break

            if account_payroll:
                debit_line_3 = (0, 0, {
                    'name': "Total Payslip Deserved Amount",
                    'partner_id': record.employee_id.address_home_id.id,
                    'account_id': payroll_account,
                    'journal_id': record.expense_journal_id.id,
                    'date': record.expense_date,
                    'debit': record.request_id.total_payslip_deserved_amount > 0.0 and record.request_id.total_payslip_deserved_amount or 0.0,
                    'credit': record.request_id.total_payslip_deserved_amount < 0.0 and -record.request_id.total_payslip_deserved_amount or 0.0,
                })
                line_ids.append(debit_line_3)

            account_payroll2 = self.env["type.allowances"].search([('type', '=', 'payroll')], limit=1)
            if not account_payroll2 or not account_payroll2.line_ids:
                raise exceptions.ValidationError(
                    _("No payroll account lines configured. Please check the 'type.allowances' settings for payroll."))
            payroll_account2 = []
            for allowances in account_payroll2.line_ids:
                if allowances.structure_id.id == record.employee_id.contract_id.struct_id.id:
                    payroll_account2 = allowances.account_type_allowances_id.id
                    break

            if account_payroll2:
                debit_line_4 = (0, 0, {
                    'name': "Last Month Worked Days Amount",
                    'partner_id': record.employee_id.address_home_id.id,
                    'account_id': payroll_account2,
                    'journal_id': record.expense_journal_id.id,
                    'date': record.expense_date,
                    'debit': record.request_id.last_month_worked > 0.0 and record.request_id.last_month_worked or 0.0,
                    'credit': record.request_id.last_month_worked < 0.0 and -record.request_id.last_month_worked or 0.0,
                })
                line_ids.append(debit_line_4)

            account_amount_due = self.env["type.allowances"].search([('type', '=', 'eamountdue')], limit=1)
            if account_amount_due:
                debit_line_8 = (0, 0, {
                    'name': "ESR Deserved Amount",
                    'partner_id': record.employee_id.address_home_id.id,
                    'account_id': account_amount_due.line_ids[0].account_type_allowances_id.id,
                    'journal_id': record.expense_journal_id.id,
                    'date': record.expense_date,
                    'debit': record.request_id.total_deserved_amount,
                })
                line_ids.append(debit_line_8)
            else:
                raise exceptions.ValidationError(
                    _("Enter the account in Amount Due Allowance Type"))

            for line_allow in record.request_id.allows_ids:
                account = line_allow.type_allowances.account.id
                if account:
                    debit_line_5 = (0, 0, {
                        'name': line_allow.type_allowances.name,
                        'partner_id': record.employee_id.address_home_id.id,
                        'account_id': account,
                        'journal_id': record.expense_journal_id.id,
                        'date': record.expense_date,
                        'debit': line_allow.other_allowances > 0.0 and line_allow.other_allowances or 0.0,
                        'credit': line_allow.other_allowances < 0.0 and -line_allow.other_allowances or 0.0,
                    })
                    line_ids.append(debit_line_5)
            for line_deduc in record.request_id.deduct_ids:
                account = line_deduc.type_detuction.account.id
                if account:
                    debit_line_6 = (0, 0, {
                        'name': line_deduc.type_detuction.name,
                        'partner_id': record.employee_id.address_home_id.id,
                        'account_id': account,
                        'journal_id': record.expense_journal_id.id,
                        'date': record.expense_date,
                        'credit': line_deduc.detuction,
                    })
                    line_ids.append(debit_line_6)

            account_loan = self.env["type.allowances"].search([('type', '=', 'loan')], limit=1)
            if account_loan:
                if account_loan.is_type_collected:
                    ac_loan = account_loan.line_ids[0].account_type_allowances_id.id
                else:
                    ac_loan = account_loan.account.id
                if not account_loan:
                    raise exceptions.ValidationError(
                        _("Enter the account in Loan Allowance Type"))
                total_deductions = record.request_id.deduction_loan

                debit_line_7 = (0, 0, {
                    'name': "Deduction Loan",
                    'partner_id': record.employee_id.address_home_id.id,
                    'account_id': ac_loan,
                    'journal_id': record.expense_journal_id.id,
                    'date': record.expense_date,
                    'credit':total_deductions,
                })
                line_ids.append(debit_line_7)
            # ////////////////////////////////////////////////////////////////////
            # 🔹 NEW SECTION: Ticket Type Handling
            account_ticket = self.env["type.allowances"].search([('type', '=', 'ticket')], limit=1)
            if account_ticket:
                if account_ticket.is_type_collected==False:
                    ac_ticket = account_ticket.line_ids and account_ticket.line_ids[
                        0].account_type_allowances_id.id or False
                else:
                    ac_ticket = account_ticket.account.id
                if not ac_ticket:
                    raise exceptions.ValidationError(_("Enter the account in Ticket Allowance Type"))

                total_ticket_amount = sum(record.request_id.tick_ids.mapped('ticket'))
                if total_ticket_amount:
                    debit_line_ticket = (0, 0, {
                        'name': "Employee Ticket Settlement",
                        'partner_id': record.employee_id.address_home_id.id,
                        'account_id': ac_ticket,
                        'journal_id': record.expense_journal_id.id,
                        'date': record.expense_date,
                        'debit': total_ticket_amount > 0.0 and total_ticket_amount or 0.0,
                        'credit': total_ticket_amount < 0.0 and -total_ticket_amount or 0.0,
                    })
                    line_ids.append(debit_line_ticket)

            account_allowances = self.env["type.allowances"].search([('type', '=', 'allwances')], limit=1)
            if account_allowances:
                allowances_account = account_allowances.line_ids[0].account_type_allowances_id.id
                allowances_line = (0, 0, {
                    'name': "Employee Allowances",
                    'partner_id': record.employee_id.address_home_id.id,
                    'account_id': allowances_account,
                    'journal_id': record.expense_journal_id.id,
                    'date': record.expense_date,
                    'debit': record.request_id.other_allowance > 0.0 and record.request_id.other_allowance or 0.0,
                    'credit': record.request_id.other_allowance < 0.0 and -record.request_id.other_allowance or 0.0,
                })
                line_ids.append(allowances_line)

            if record.request_id.pt_cash_account_id:
                pt_cash_line = (0, 0, {
                    'name': "PT Cash",
                    'partner_id': record.employee_id.address_home_id.id,
                    'account_id': record.request_id.pt_cash_account_id.id,
                    'journal_id': record.expense_journal_id.id,
                    'date': record.expense_date,
                    'debit': -record.request_id.pt_cash_balance if record.request_id.pt_cash_balance < 0 else 0.0,
                    'credit': record.request_id.pt_cash_balance if record.request_id.pt_cash_balance > 0 else 0.0,
                })
                line_ids.append(pt_cash_line)

            account_deduction = self.env["type.allowances"].search([('type', '=', 'deduction')], limit=1)
            if account_deduction:
                deduction_line = (0, 0, {
                    'name': "Employee Deduction",
                    'partner_id': record.employee_id.address_home_id.id,
                    'account_id': account_deduction.line_ids[0].account_type_allowances_id.id,
                    'journal_id': record.expense_journal_id.id,
                    'date': record.expense_date,
                    'debit': record.request_id.other_deduction < 0.0 and -record.request_id.other_deduction or 0.0,
                    'credit': record.request_id.other_deduction > 0.0 and record.request_id.other_deduction or 0.0,
                })
                line_ids.append(deduction_line)

            # /////////////////////////////////////////////////////////////////////////

            # ✅ Create Journal Entry
            move_dict = {
                'ref': _('Ending Service Reward Settlement for %s') % record.employee_id.name,
                'journal_id': record.expense_journal_id.id,
                'date': record.expense_date,
                'line_ids': line_ids,
            }

            move = self.env['account.move'].with_context(check_move_validity=False).create(move_dict)
            record.request_id.write({'account_move_id': move.id})

    def settle_employee_reward(self):
        """Function to create the account.payment (payment entry) and update state."""
        for record in self:
            if not record.employee_id.address_home_id:
                raise exceptions.ValidationError(
                    _("This employee has no private address, please add it to the employee profile!"))

            # Create payment entry (account.payment)
            name = _('Ending service reward payment of %s') % (record.employee_id.name)
            payment_dict = {
                'reward_id': record.request_id.id,
                'payment_type': 'outbound',
                'partner_type': 'supplier',
                'amount': record.amount,
                'journal_id': record.settlement_journal_id.id,
                'partner_id': record.employee_id.address_home_id.id,
                'date': record.payment_date,
            }
            payment_id = self.env['account.payment'].create(payment_dict)
            payment_id.action_post()
            record.request_id.write({'payment_id': payment_id.id, 'state': 'paid'})


class Payment(models.Model):
    _name = 'account.payment'
    _inherit = 'account.payment'

    reward_id = fields.Many2one(comodel_name="hr.end.service.benefit", string="", required=False, )

    def action_post(self):
        res = super(Payment, self).action_post()
        for record in self:
            record.reward_id.state = 'paid'
        return res

    def name_get(self):
        new_format = []
        for rec in self:
            if rec.name:
                result = rec.name
            else:
                result = rec.partner_id.name + ' Payment'
            new_format.append((rec.id, result))
        return new_format
