# -*- coding: utf-8 -*-

##############################################################################
#    Maintainer: Eng.Mohamed Abdalla <mohamedabdalla142001@gmail.com>
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
from datetime import date
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class EmployeeVacationSettlement(models.Model):
    _name = "employee.vacation.settlement"
    _description = "Employee Vacation Settlement"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _default_journal_id(self):
        """ The journal is determining the company of the accounting entries generated from expense. We need to force journal company and expense sheet company to be the same. """
        default_company_id = self.default_get(['company_id'])['company_id']
        journal = self.env['account.journal'].search([('is_vacation', '=', True)], limit=1)
        return journal.id

    def _default_type_amount_due(self):
        amount_default = self.env['type.allowances'].search([('type', '=', 'amountdue')], limit=1)
        return amount_default

    def _default_type_ticket(self):
        ticket_default = self.env['type.allowances'].search([('type', '=', 'ticket')], limit=1)
        return ticket_default

    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    department_id = fields.Many2one(related='employee_id.department_id', string='Department', store=True)
    job_id = fields.Many2one(related='employee_id.job_id', string='Position', store=True)
    # partner_emp = fields.Many2one(related='employee_id.address_home_id', string='Partner Related', store=True)
    job_title = fields.Char(related='employee_id.job_title', string='Position Number', store=True)
    register_num = fields.Char(related='employee_id.registration_number2', string='Registration Number of the Employee',
                               store=True)
    current_contract_id = fields.Many2one('hr.contract', string='Current Contract',
                                          default=lambda self: self.env.context.get('active_id'),
                                          domain="[('employee_id', '=', employee_id)]")
    start_date_work = fields.Date(related='current_contract_id.date_start', string="Start Date", store=True)
    total_salary = fields.Monetary(related='current_contract_id.total_package_val', string='Total Salary Value',
                                   currency_field='currency_id', readonly=True, store=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    leave_id = fields.Many2one('hr.leave', string="Leave", required=True,
                               domain="[('state', '=', 'validate'), ('employee_id', '=', employee_id),('holiday_status_id.work_entry_type_id.code', '=', 'LEAVE120')]")
    leave_start_date = fields.Date(related='leave_id.request_date_from', string='Leave Start Date', store=True)
    leave_end_date = fields.Date(related='leave_id.request_date_to', string='Number of Vacation Days', store=True)
    last_leave_end_date = fields.Date(string='Last Leave End Date', store=True)
    annual_vacation_days = fields.Float(string='Annual Vacation Days', readonly=False)

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        for record in self:
            if record.employee_id:
                # Assuming you can access the latest contract
                contract = record.employee_id.contract_id
                if contract and contract.date_start:
                    start_date = contract.date_start
                    today = date.today()
                    years_difference = (today - start_date).days / 365.25  # Account for leap years
                    if years_difference < 5:
                        record.annual_vacation_days = 21.0
                    else:
                        record.annual_vacation_days = 30.0
                else:
                    # Default if no contract start date is found
                    record.annual_vacation_days = 21.0

    num_of_vacation = fields.Integer(string='Number of Vacation Days', compute='_compute_num_of_vacation',
                                     readonly=True)
    last_work_date = fields.Date(string='Date of Last Work')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('send', 'sent'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('pay_progress', 'Payment in progress'),
        ('journal_draft', 'Journal Entry Draft'),
        ('post', 'Posted'),
        ('done', 'Done'),
        ('pay', 'Payed'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', track_visibility='onchange', copy=False)
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    number_of_days_of_allowances = fields.Float(related='leave_id.number_of_days_display',
                                                string='The number of days due from the forecast to date',
                                                readonly=True, compute="")
    financially_accrued_leave = fields.Integer(string='Financially Accrued Leave')
    remaining_vacation_balance_after_settlement = fields.Integer(
        string='The remaining vacation balance after settlement is financial', compute='_balance_after_financial')
    remaining_vacation_balance_working_days = fields.Integer(string='The remaining vacation balance after working days',
                                                             compute='_balance_after_working_days')
    contract_type = fields.Many2one(related='current_contract_id.contract_type_id', string='Contract Type', store=True)
    contract_period = fields.Date(related='current_contract_id.trial_date_end', string='Contract Period', store=True)
    vacation_allowance_pay = fields.Monetary(related='current_contract_id.vacation_total_amount',
                                             string='Vacation Allowance Pay')
    todays_pay = fields.Monetary(string="Today's Pay", compute='_compute_todays_pay')
    amount_due = fields.Float(string='Amount Due', compute='_compute_amount_due')
    end_date_work = fields.Date(related='current_contract_id.date_end', string="End Date", store=True)
    ticket1 = fields.Boolean(related='current_contract_id.ticket1')
    tickets_no_company = fields.Integer(string="No. Of Tickets", related='current_contract_id.tickets_no_company')
    # tickets_val_company = fields.Integer(string="Tickets Value")
    tickets_val_company = fields.Integer(
        string="Tickets Value",
        compute="_compute_tickets_val_company",
        store=True,
    )

    @api.depends('employee_id')
    def _compute_tickets_val_company(self):
        for rec in self:
            # Get current active contract of this employee
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', '=', 'open')
            ], limit=1)
            rec.tickets_val_company = contract.tickets_val_company if contract else 0

    allowance_ids = fields.One2many('employee.vacation.settlement.allowance', 'settlement_id', string="Allowances", )
    total_allowances = fields.Monetary(string="Total Allowances", compute='_compute_total_allowances', store=True)
    detuction_ids = fields.One2many('employee.vacation.settlement.detuction', 'settlement_id', string="Detuctions")
    total_detuction = fields.Monetary(string="Total Detuction", compute='_compute_total_detuction', store=True)
    recipient_users = fields.Text()
    total_employee_id = fields.One2many('total.employee', 'settlement_ids', string="Total Employee")
    type_allowances = fields.Many2one('type.allowances', string="Type of Allowance", ondelete='cascade',
                                      domain=[('type', '=', 'allwances')], store=True)
    type_detuction = fields.Many2one('type.allowances', string="Type of Detuction", ondelete='cascade',
                                     domain=[('type', '=', 'deduction')]
                                     )
    type_amount_due = fields.Many2one('type.allowances', string="Type of Amount Due", required=True, ondelete='cascade',
                                      domain=[('type', '=', 'amountdue')], store=True,
                                      default=_default_type_amount_due,
                                      )
    type_ticket = fields.Many2one('type.allowances', string="Type of Amount Due", required=False, ondelete='cascade',
                                  domain=[('type', '=', 'ticket')], store=True,
                                  default=_default_type_ticket,
                                  )

    account_move_id = fields.Many2one('account.move', string='Journal Entry', compute="_compute_account_move_id")
    name_account_move = fields.Char(related='account_move_id.name', string="Journal Entries Name")
    vacation_end_service = fields.Boolean()
    vacation_source = fields.Char()
    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Company")
    ], default='own_account', tracking=True,
        states={'done': [('readonly', True)], 'approved': [('readonly', True)], 'reported': [('readonly', True)]},
        string="Paid By")
    journal_id = fields.Many2one('account.journal', string='vacation Journal', domain="[('is_vacation', '=', True)]",
                                 default=_default_journal_id, help="The journal used when the expense is done.")

    journall = fields.Many2one('account.journal', string='Journall', domain=[('type', '=', 'general')])

    analytic = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        compute="_compute_analytic",
        store=True,
    )

    @api.depends('employee_id')
    def _compute_analytic(self):
        for rec in self:
            # Find current active contract for this employee
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', 'in', ['open', 'active'])
            ], limit=1)
            rec.analytic = contract.analytic_account_id.id if contract.analytic_account_id else False

    account_id = fields.Many2one(
        'account.account',
        store=True,
        readonly=False,
        precompute=True,
        string='Account',
        help="An expense account is expected"
    )
    total_total = fields.Float(string="Total", compute='_compute_total')
    total_total_word = fields.Char(string="Total in Words", compute='_compute_total_total_word')

    sent_date = fields.Date(string="Send Date")
    submit_date = fields.Date(string="Submit Date")
    payment_date = fields.Date(string="Payment Date")

    def _compute_account_move_id(self):
        for rec in self:
            if rec.state == 'post' or rec.state == 'pay':
                rec.account_move_id = self.env['account.move'].search([('ref', '=', self.name)], limit=1)
            else:
                rec.account_move_id = False

    @api.depends('amount_due', 'total_allowances', 'tickets_val_company', 'total_detuction')
    def _compute_total(self):
        for record in self:
            record.total_total = (
                    record.amount_due +
                    record.total_allowances +
                    record.tickets_val_company -
                    record.total_detuction
            )

    @api.onchange('leave_id')
    def _compute_number_of_days_of_allowances(self):
        for record in self:
            if record.leave_id:
                record.number_of_days_of_allowances = record.leave_id.number_of_days_display
            else:
                record.number_of_days_of_allowances = 0.0



    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('employee.vacation.settlement') or _('New')
        if self.env.context.get('from_end_service_menu'):
            vals['vacation_end_service'] = True
            vals['annual_vacation_days'] = 21.0
        return super(EmployeeVacationSettlement, self).create(vals)

    @api.onchange('last_work_date')
    def _check_last_work_date(self):
        for record in self:
            if record.last_work_date and record.leave_start_date:
                if record.last_work_date >= record.leave_start_date:
                    if record.last_work_date > record.leave_start_date:
                        raise ValidationError("The Date of Last Work must be before the Leave Start Date.")
                    else:
                        raise ValidationError("The Date of Last Work can't be the Leave Start Date.")

    @api.onchange('leave_end_date')
    def _compute_num_of_vacation(self):
        for record in self:
            if record.leave_start_date and record.leave_end_date:
                delta = (record.leave_end_date - record.leave_start_date)
                record.num_of_vacation = delta.days + 1

    @api.depends('financially_accrued_leave', 'number_of_days_of_allowances')
    @api.onchange('financially_accrued_leave')
    def _balance_after_financial(self):
        for record in self:
            x = float(record.number_of_days_of_allowances)
            record.remaining_vacation_balance_after_settlement = int(x) - record.financially_accrued_leave

    @api.onchange('financially_accrued_leave')
    def _balance_after_working_days(self):
        for record in self:
            x = float(record.number_of_days_of_allowances)
            record.remaining_vacation_balance_working_days = int(x) - record.num_of_vacation

    @api.onchange('employee_id')
    def _compute_all_allowances(self):
        type = self.env['type.allowances'].search([('type', '=', 'allwances')])
        line = [(5, 0, 0)]
        for record in type:
            val = {
                'type_allowances': record.id,
            }
            line.append((0, 0, val))
            self.allowance_ids = line

    @api.onchange('employee_id')
    def _compute_all_detuction(self):
        type = self.env['type.allowances'].search([('type', '=', 'deduction')])
        line = [(5, 0, 0)]
        for record in type:
            val = {
                'type_detuction': record.id,
            }
            line.append((0, 0, val))
            self.detuction_ids = line

    @api.depends('allowance_ids.other_allowances')
    @api.onchange('allowance_ids')
    def _compute_total_allowances(self):
        for record in self:
            total = 0
            for allowance in record.allowance_ids:
                total += allowance.other_allowances
            record.total_allowances = total

    @api.depends('detuction_ids.detuction')
    @api.onchange('detuction_ids')
    def _compute_total_detuction(self):
        for record in self:
            total = 0
            for detuction in record.detuction_ids:
                total += detuction.detuction
            record.total_detuction = total

    @api.onchange('vacation_allowance_pay')
    def _compute_todays_pay(self):
        for record in self:
            record.todays_pay = record.vacation_allowance_pay / 30

    @api.onchange('financially_accrued_leave')
    def _compute_amount_due(self):
        for line in self:
            line.amount_due = line.todays_pay * line.financially_accrued_leave

    def action_reset_to_draft(self):
        return self.write({'state': 'draft'})

    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_submit(self):
        for record in self:
            record.write({'state': 'submit'})
            record.submit_date = fields.Datetime.now()

    def action_sent(self):
        for record in self:
            record.write({'state': 'send'})
            record.sent_date = fields.Datetime.now()

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_approve(self):
        self.write({'state': 'approve'})

    def action_payment_in_progress(self):
        for record in self:
            record.write({'state': 'pay_progress'})
            record.payment_date = fields.Datetime.now()

    @api.depends('total_total', 'currency_id')
    def _compute_total_total_word(self):
        for record in self:
            if record.total_total and record.currency_id:
                record.total_total_word = record.total_amount_in_words('ar_AA', record.total_total)
            else:
                record.total_total_word = ""

    def total_amount_in_words(self, lang, total_total):
        self.ensure_one()  # Ensure the record is a singleton
        return self.currency_id.with_context(lang=lang).amount_to_text(total_total)


    def action_sheet_move_create(self):
        self.ensure_one()  # Ensure we are working on a single record

        # Find the draft journal entry related to this record
        move = self.env['account.move'].search([
            ('ref', '=', self.name),
            ('state', '=', 'draft')
        ], limit=1)

        if not move:
            raise UserError(_("No draft journal entry found for this settlement."))

        # Post the journal entry
        move.action_post()

        # Update the settlement state
        self.write({'state': 'post'})

    def action_sheet_move_create_draft(self):
        for sheet in self:
            # Ensure state
            if sheet.state not in ('approve', 'pay_progress'):
                raise UserError(_("You can only generate accounting entry for approved settlement(s)."))

            if not sheet.employee_id.sudo().address_home_id:
                raise UserError(
                    _("The private address of the employee is required to post the settlement. Please add it on the employee form."))

            # Determine journal
            journal = sheet.journal_id or sheet.company_id.expense_journal_id
            if not journal:
                # fallback to a general journal
                journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
            if not journal:
                raise UserError(_("No valid journal found for this operation."))

            # Build move header
            move_vals = {
                'journal_id': journal.id,
                'date': fields.Date.context_today(self),
                'ref': sheet.name,
                # 'analytic_distribution': {sheet.analytic.id: 100.0} if sheet.analytic else {},

                'line_ids': [],
            }

            total_debit = 0
            total_credit = 0

            # Allowances
            for line in sheet.allowance_ids:
                if not line.type_allowances.line_ids:
                    raise UserError(_("Account for type allowances not found."))
                move_vals['line_ids'].append((0, 0, {
                    'account_id': line.type_allowances.line_ids[0].account_type_allowances_id.id,
                    'partner_id': sheet.employee_id.address_home_id.id,
                    'name': line.other_allowances_note or 'Allowance',
                    'debit': line.other_allowances,
                    'credit': 0,
                    'analytic_distribution': {sheet.analytic.id: 100.0} if sheet.analytic else {},
                }))
                total_debit += line.other_allowances

            # Deductions
            employee_structure = sheet.employee_id.contract_id.struct_id
            for line in sheet.detuction_ids:
                account_id = False
                if line.type_detuction:
                    # try to get from type.allowances.line (structure-specific)
                    if employee_structure:
                        structure_line = line.type_detuction.line_ids.filtered(
                            lambda l: l.structure_id == employee_structure
                        )
                        if structure_line and structure_line.account_type_allowances_id:
                            account_id = structure_line.account_type_allowances_id.id
                    # fallback
                    if not account_id and line.type_detuction.account:
                        account_id = line.type_detuction.account.id

                if not account_id:
                    raise UserError(_("Account for type deduction not found for employee structure."))

                move_vals['line_ids'].append((0, 0, {
                    'account_id': account_id,
                    'partner_id': sheet.employee_id.address_home_id.id,
                    'name': line.detuction_note or 'Deduction',
                    'debit': 0,
                    'credit': line.detuction,
                    'analytic_distribution': {sheet.analytic.id: 100.0} if sheet.analytic else {},
                }))
                total_credit += line.detuction

            # Amount Due
            amount_due = sheet.amount_due or 0.0
            if sheet.type_amount_due.line_ids:
                move_vals['line_ids'].append((0, 0, {
                    'account_id': sheet.type_amount_due.line_ids[0].account_type_allowances_id.id,
                    'partner_id': sheet.employee_id.address_home_id.id,
                    'name': _("Amount Due"),
                    'debit': amount_due,
                    'credit': 0,
                    'analytic_distribution': {sheet.analytic.id: 100.0} if sheet.analytic else {},
                }))
                total_debit += amount_due

            # Ticket
            ticket = self.tickets_val_company or 0.0
            if self.type_ticket and self.type_ticket.account:
                move_vals['line_ids'].append((0, 0, {
                    'account_id': self.type_ticket.account.id,
                    'partner_id': self.employee_id.address_home_id.id,
                    'name': _("Ticket Value"),
                    'debit': ticket,
                    'credit': 0,
                    'analytic_distribution': {self.analytic.id: 100.0}
                }))
                total_debit += ticket

            # Balancing line
            balancing_amount = total_debit - total_credit

            # determine balancing account based on journal type
            if journal.type == 'general':
                balancing_account = journal.gs_def_credit_acc
            elif journal.type == 'purchase':
                balancing_account = journal.default_account_id
            else:
                balancing_account = False

            if not balancing_account:
                raise UserError(_("No balancing account found on the selected journal."))

            # ✅ Use a payable account instead of journal account
            payable_account = sheet.employee_id.address_home_id.property_account_payable_id
            if not payable_account:
                raise UserError(_("Employee partner has no payable account configured."))

            move_vals['line_ids'].append((0, 0, {
                'account_id': payable_account.id,
                'partner_id': sheet.employee_id.address_home_id.id,
                'name': _('Employee Payable'),
                'debit': 0 if balancing_amount > 0 else abs(balancing_amount),
                'credit': balancing_amount if balancing_amount > 0 else 0,
            }))

            # Create the draft journal entry
            move = self.env['account.move'].create(move_vals)
            sheet.write({'state': 'journal_draft'})

    def action_open_account_move(self):
        self.ensure_one()
        AccountMove = self.env['account.move'].search([('ref', '=', self.name)], limit=1)
        return {
            'name': AccountMove.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [[False, "form"]],
            'res_model': 'account.move',
            'res_id': AccountMove.id,
        }

    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        There can be more than one bank_account_id in the expense sheet when registering payment for multiple expenses.
        The default_partner_bank_id is set only if there is one available, if more than one the field is left empty.
        :return: An action opening the account.payment.register wizard.
        '''
        AccountMove = self.env['account.move'].search([('ref', '=', self.name)], limit=1)

        self.write({'state': 'pay'})
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.account_move_id.ids,
                'default_partner_bank_id': self.employee_id.sudo().bank_account_id.id,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',

        }

    # allowances model


class EmployeeVacationSettlementAllowance(models.Model):
    _name = 'employee.vacation.settlement.allowance'
    _description = 'Employee Vacation Settlement Allowance'

    account_id = fields.One2many('account.move.line', 'allowance_ids', string='Matched Journal Items', store=True)
    settlement_id = fields.Many2one('employee.vacation.settlement', string='Vacation Settlement',
                                    ondelete='cascade')
    other_allowances = fields.Monetary(string="Other Allowances", store=True)
    other_allowances_note = fields.Text(string='Description')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    type_allowances = fields.Many2one('type.allowances', string="Type of Allowance", required=True, ondelete='cascade',
                                      domain=[('type', '=', 'allwances')], store=True)

# //////////////////////////////////////////////////////////////

class EmployeeVacationSettlementTicket(models.Model):
        _name = 'employee.vacation.settlement.ticket'
        _description = 'Employee Vacation Settlement Ticket'

        account_id = fields.One2many('account.move.line', 'ticket_ids', string='Matched Journal Items', store=True)
        settlement_id = fields.Many2one('employee.vacation.settlement', string='Vacation Settlement',
                                        ondelete='cascade')
        ticket = fields.Monetary(string="Ticket", store=True)
        ticket_note = fields.Text(string='Description')
        currency_id = fields.Many2one('res.currency', string='Currency',
                                      default=lambda self: self.env.company.currency_id)
        type_ticket = fields.Many2one('type.allowances', string="Type of Ticket", required=True,
                                          ondelete='cascade',
                                          domain=[('type', '=', 'ticket')], store=True)


# ///////////////////////////////////////////////////////////////////
class EmployeeVacationSettlementDetuction(models.Model):
    _name = 'employee.vacation.settlement.detuction'
    _description = 'Employee Vacation Settlement Deduction'

    settlement_id = fields.Many2one(
        'employee.vacation.settlement',
        string='Deduction Settlement',
        ondelete='cascade'
    )

    type_detuction = fields.Many2one(
        'type.allowances',
        string="Type of Deduction",
        required=True,
        ondelete='cascade',
        domain=[('type', '=', 'deduction')]
    )
    detuction = fields.Monetary(
        string="Deduction Money",
        currency_field='currency_id',
        # compute='_compute_balance',
        store=True
    )
    detuction_note = fields.Text(string='Description')
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    account_id = fields.One2many(
        'account.move.line',
        'allowance_ids',
        string='Matched Journal Items',
        store=True
    )

    # @api.depends('account_id.balance', 'settlement_id.employee_id', 'type_detuction', 'type_detuction.account',
    #              'type_detuction.is_loan')
    # def _compute_balance(self):
    #     for record in self:
    #         print(f"Computing detuction for record {record.id}")
    #         record.detuction = 0  # Reset value
    #
    #         if record.settlement_id and record.settlement_id.employee_id:
    #             employee_partner_id = record.settlement_id.employee_id.address_home_id.id
    #
    #             if record.type_detuction and record.type_detuction.account:
    #                 cash_advance_lines = self.env['account.move.line'].search([
    #                     ('partner_id', '=', employee_partner_id),
    #                     ('account_id', '=', record.type_detuction.account.id)
    #                 ])
    #                 record.detuction = sum(cash_advance_lines.mapped('balance'))
    #
    #         if record.type_detuction.is_loan:
    #             if record.settlement_id and record.settlement_id.employee_id:
    #                 employee_loans = self.env['employee.loan'].search([
    #                     ('employee_id', '=', record.settlement_id.employee_id.id)
    #                 ])
    #
    #                 total_deduction = sum(
    #                     installment.installment_amt for loan in employee_loans
    #                     for installment in loan.installment_lines.filtered(lambda line: not line.payroll_name)
    #                 )
    #                 record.detuction += total_deduction


class TypeAllowances(models.Model):
    _name = 'type.allowances'
    _description = 'Type of Allowance'


    name = fields.Char(string='Allowance Type')
    type = fields.Selection(string='Type', selection=[('deduction', 'Deduction'), ('allwances', 'Allowances'),
                                                      ('amountdue', 'VS Amount Due'), ('ticket', 'Ticket'),
                                                      ('holidays', 'EOS Holidays'), ('payroll', 'EOS Payslip'), ('loan', 'EOS Loan'),
                                                      ('eamountdue', 'EOS Amount Due') ])
    account = fields.Many2one('account.account', string='Chart of Account', required=False,
                              domain=[('deprecated', '=', False)])
    is_type_collected = fields.Boolean(string='Is Amount Collected  With Other ?', required=False, default=True)
    description = fields.Text(string='Description')
    is_loan = fields.Boolean()
    line_ids = fields.One2many('type.allowances.line', 'type_allowances_id', string="Structure Accounts")

class TimeoffConfLine(models.Model):
    _name = "type.allowances.line"
    _description = "Ticket Config Line"

    type_allowances_id = fields.Many2one('type.allowances', string="Type of Allowance", ondelete='cascade')
    structure_id = fields.Many2one('hr.payroll.structure', string="Salary Structure", required=True)
    account_type_allowances_id = fields.Many2one('account.account', string="Account")



class AccountMoveLine(models.Model):
    _inherit = 'account.account'

    is_allowances = fields.Boolean()


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    settlement_id = fields.Many2one('employee.vacation.settlement', string='Vacation Settlement', required=True,
                                    ondelete='cascade')
    allowance_ids = fields.Many2one('employee.vacation.settlement.allowance', string="Allowances")

    ticket_ids = fields.Many2one('employee.vacation.settlement.ticket', string="Ticket")


class Total(models.Model):
    _name = 'total.employee'
    _description = 'Total Employee'  # Added description

    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    total_allowances = fields.Monetary(string="Total Allowances",
                                       related='settlement_ids.total_allowances')  # Completed field definition
    tickets_val_company = fields.Integer(string="Tickets Value Company",
                                         related='settlement_ids.tickets_val_company')  # Completed field definition
    total_detuction = fields.Monetary(string="Total Detuction",
                                      related='settlement_ids.total_detuction')  # Completed field definition
    settlement_ids = fields.Many2one('employee.vacation.settlement', string="Vacation Settlements", required=True,
                                     ondelete='cascade')  # Added One2many field
    amount_due = fields.Float(string="Total amount Due", related='settlement_ids.amount_due')
