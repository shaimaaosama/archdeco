# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    employee_loan_id = fields.Many2one('employee.loan',)

    def action_validate(self):
        res = super().action_validate()
        self.employee_loan_id.state = 'paid'
        return res

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        if self.employee_loan_id:
            ''' Prepare the dictionary to create the default account.move.lines for the current payment.
            :param write_off_line_vals: Optional list of dictionaries to create a write-off account.move.line easily containing:
                * amount:       The amount to be added to the counterpart amount.
                * name:         The label to set on the line.
                * account_id:   The account on which create the write-off.
            :param force_balance: Optional balance.
            :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
            '''
            self.ensure_one()
            write_off_line_vals = write_off_line_vals or []

            if not self.outstanding_account_id:
                raise UserError(_(
                    "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %(payment_method)s payment method in the %(journal)s journal.",
                    payment_method=self.payment_method_line_id.name, journal=self.journal_id.display_name))

            # Compute amounts.
            write_off_line_vals_list = write_off_line_vals or []
            write_off_amount_currency = sum(x['amount_currency'] for x in write_off_line_vals_list)
            write_off_balance = sum(x['balance'] for x in write_off_line_vals_list)

            if self.payment_type == 'inbound':
                # Receive money.
                liquidity_amount_currency = self.amount
            elif self.payment_type == 'outbound':
                # Send money.
                liquidity_amount_currency = -self.amount
            else:
                liquidity_amount_currency = 0.0

            if not write_off_line_vals and force_balance is not None:
                sign = 1 if liquidity_amount_currency > 0 else -1
                liquidity_balance = sign * abs(force_balance)
            else:
                liquidity_balance = self.currency_id._convert(
                    liquidity_amount_currency,
                    self.company_id.currency_id,
                    self.company_id,
                    self.date,
                )
            counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
            counterpart_balance = -liquidity_balance - write_off_balance
            currency_id = self.currency_id.id

            # Compute a default label to set on the journal items.
            liquidity_line_name = ''.join(x[1] for x in self._get_aml_default_display_name_list())
            counterpart_line_name = ''.join(x[1] for x in self._get_aml_default_display_name_list())

            line_vals_list = [
                # Liquidity line.
                {
                    'name': liquidity_line_name,
                    'date_maturity': self.date,
                    'amount_currency': liquidity_amount_currency,
                    'currency_id': currency_id,
                    'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                    'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.outstanding_account_id.id,
                },
                # Receivable / Payable.
                {
                    'name': counterpart_line_name,
                    'date_maturity': self.date,
                    'amount_currency': counterpart_amount_currency,
                    'currency_id': currency_id,
                    'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                    'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.employee_loan_id.loan_type_id.payable_emp_account.id,
                },
            ]
            return line_vals_list + write_off_line_vals_list
        else:
            # ''' Prepare the dictionary to create the default account.move.lines for the current payment.
            # :param write_off_line_vals: Optional list of dictionaries to create a write-off account.move.line easily containing:
            #     * amount:       The amount to be added to the counterpart amount.
            #     * name:         The label to set on the line.
            #     * account_id:   The account on which create the write-off.
            # :param force_balance: Optional balance.
            # :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
            # '''
            # self.ensure_one()
            # write_off_line_vals = write_off_line_vals or []
            #
            # if not self.outstanding_account_id:
            #     raise UserError(_(
            #         "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %(payment_method)s payment method in the %(journal)s journal.",
            #         payment_method=self.payment_method_line_id.name, journal=self.journal_id.display_name))
            #
            # # Compute amounts.
            # write_off_line_vals_list = write_off_line_vals or []
            # write_off_amount_currency = sum(x['amount_currency'] for x in write_off_line_vals_list)
            # write_off_balance = sum(x['balance'] for x in write_off_line_vals_list)
            #
            # if self.payment_type == 'inbound':
            #     # Receive money.
            #     liquidity_amount_currency = self.amount
            # elif self.payment_type == 'outbound':
            #     # Send money.
            #     liquidity_amount_currency = -self.amount
            # else:
            #     liquidity_amount_currency = 0.0
            #
            # if not write_off_line_vals and force_balance is not None:
            #     sign = 1 if liquidity_amount_currency > 0 else -1
            #     liquidity_balance = sign * abs(force_balance)
            # else:
            #     liquidity_balance = self.currency_id._convert(
            #         liquidity_amount_currency,
            #         self.company_id.currency_id,
            #         self.company_id,
            #         self.date,
            #     )
            # counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
            # counterpart_balance = -liquidity_balance - write_off_balance
            # currency_id = self.currency_id.id
            #
            # # Compute a default label to set on the journal items.
            # liquidity_line_name = ''.join(x[1] for x in self._get_aml_default_display_name_list())
            # counterpart_line_name = ''.join(x[1] for x in self._get_aml_default_display_name_list())
            #
            # line_vals_list = [
            #     # Liquidity line.
            #     {
            #         'name': liquidity_line_name,
            #         'date_maturity': self.date,
            #         'amount_currency': liquidity_amount_currency,
            #         'currency_id': currency_id,
            #         'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
            #         'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
            #         'partner_id': self.partner_id.id,
            #         'account_id': self.outstanding_account_id.id,
            #     },
            #     # Receivable / Payable.
            #     {
            #         'name': counterpart_line_name,
            #         'date_maturity': self.date,
            #         'amount_currency': counterpart_amount_currency,
            #         'currency_id': currency_id,
            #         'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
            #         'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
            #         'partner_id': self.partner_id.id,
            #         'account_id': self.destination_account_id.id,
            #     },
            # ]
            # return line_vals_list + write_off_line_vals_list
            return super()._prepare_move_line_default_vals(write_off_line_vals=None, force_balance=None)

class employee_loan(models.Model):
    _name = 'employee.loan'
    _description = 'Loan of an Employee'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    def cash_payment(self):
        return {
            'type': 'ir.actions.act_window',
            'target': 'new',
            'name': _('Cash Payment'),
            'view_mode': 'form',
            'res_model': 'payment.cash',
        }

    loan_state=[('draft','Draft'),
                ('request','Submit Request'),
                ('dep_approval','Department Approval'),
                ('hr_approval','HR Approval'),
                ('financial_approval', 'Financial Approval'),
                ('paid', 'Paid'),
                ('done','Done'),
                ('close', 'Close'),
                ('reject','Reject'),
                ('cancel','Cancel')]
                
    @api.model
    def _get_employee(self):
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        return employee_id

    @api.model
    def _get_default_user(self):
        return self.env.user

    def send_loan_detail(self):
        self.ensure_one()
        template = self.env.ref('pt_hr_dev_loan.dev_employee_loan_detail_send_mail')
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)

        ctx = {
            'default_model': 'employee.loan',
            'default_res_ids': [self.id],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
        }

        return {
            'name': 'Send Loan Email',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

        
    @api.depends('start_date','term')
    def _get_end_date(self):
        for loan in self:
            end_date = False
            if loan.start_date and loan.term:
                start_date =  self.start_date
                end_date = start_date+relativedelta(months=self.term)
            loan.end_date = end_date

    name = fields.Char('Name',default='/',copy=False)
    state = fields.Selection(loan_state,string='State',default='draft', tracking=True)
    employee_id = fields.Many2one('hr.employee',default=_get_employee, required=True)
    department_id = fields.Many2one('hr.department',string='Department')
    hr_manager_id = fields.Many2one('hr.employee',string='Hr Manager')
    manager_id = fields.Many2one('hr.employee',string='Department Manager', required=True)
    job_id = fields.Many2one('hr.job',string="Job Position")
    date = fields.Date('Date',default=fields.Date.today())
    start_date = fields.Date('Start Date',default=fields.Date.today(),required=True)
    end_date = fields.Date('End Date',compute='_get_end_date')
    term = fields.Integer('Term',required=True)
    loan_type_id = fields.Many2one('employee.loan.type',string='Type',required=True)
    payment_method = fields.Selection([('by_payslip','By Payslip')],string='Payment Method',default='by_payslip', required=True)
    loan_amount = fields.Float('Loan Amount',required=True)
    paid_amount = fields.Float('Paid Amount', compute='get_paid_amount')
    remaing_amount = fields.Float('Remaing Amount', compute='get_remaing_amount')
    installment_amount = fields.Float('Installment Amount',required=True, compute='get_installment_amount')
    loan_url = fields.Char('URL', compute='get_loan_url')
    user_id = fields.Many2one('res.users',default=_get_default_user)
    is_apply_interest = fields.Boolean('Apply Interest')
    interest_type = fields.Selection([('liner', 'Liner'), ('reduce', 'Reduce')], string='Interest Type')
    interest_rate = fields.Float(string='Interest Rate')
    interest_amount = fields.Float('Interest Amount', compute='get_interest_amount')
    installment_lines = fields.One2many('installment.line','loan_id',string='Installments',)
    notes = fields.Text('Reason', required=True)
    is_close = fields.Boolean('IS close',compute='is_ready_to_close')
    move_id = fields.Many2one('account.move',string='Journal Entry')
    registration_number2 = fields.Char( related='employee_id.registration_number2',store=True,string='Employee Code')
    loan_document_line_ids = fields.One2many('dev.loan.document','loan_id')
    installment_count = fields.Integer(compute='get_interest_count')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    paid_by_ids = fields.Many2many('res.users', 'paid_by_ids001', string='Paid By', required=False,
                                    tracking=True)

    is_payment = fields.Boolean(compute='_compute_is_payment')

    lone_report_state_ids = fields.One2many('lone.report.state', 'employee_loan_id')

    @api.depends('installment_lines','installment_lines.payroll_paid')
    def lone_report_state(self):
        for loan in self:
            loan.lone_report_state_ids.unlink()
            name = ''
            for line in loan.installment_lines:
                if line.is_paid:
                    if line.payslip_id:
                        name = f"{line.name} - {line.payslip_id.name} - Paid"
                    else:
                        name = f"{line.name} - Paid"
                    self.env['lone.report.state'].create({
                        'name': name,
                        'employee_loan_id': loan.id,
                        'loan_line_id': line.id,
                    })
                else:
                    name = f"{line.name} - Not Paid"
                    self.env['lone.report.state'].create({
                        'name': name,
                        'employee_loan_id': loan.id,
                        'loan_line_id': line.id,})

    def _cron_update_lone_report_state_field(self):
        loans = self.search([])
        for loan in loans:
            loan.lone_report_state()


    def _compute_is_payment(self):
        for rec in self:
            rec.is_payment = False
            sum_total = 0
            payments = self.env['account.payment'].search([('employee_loan_id', '=', rec.id), ('state', '=', 'posted')])
            if payments:
                for payment in payments:
                    sum_total += payment.amount
                if sum_total == rec.loan_amount:
                    rec.is_payment = True

    def set_to_paid(self):
        self.state = 'paid'

    @api.depends('installment_lines')
    def get_interest_count(self):
        for loan in self:
            count = 0
            if loan.installment_lines:
                count = len(loan.installment_lines)
            loan.installment_count = count

    @api.onchange('term','interest_rate','interest_type')
    def onchange_term_interest_type(self):
        if self.loan_type_id:
            if self.term == 0:
                self.term = self.loan_type_id.loan_term
            self.interest_rate = self.loan_type_id.interest_rate
            self.interest_type = self.loan_type_id.interest_type
    
    @api.depends('remaing_amount')
    def is_ready_to_close(self):
        for loan in self:
            ready = False
            if loan.remaing_amount <= 0 and loan.state == 'done':
                ready = True
            loan.is_close = ready

    @api.depends('installment_lines')
    def get_paid_amount(self):
        for loan in self:
            amt = 0
            for line in loan.installment_lines:
                if line.is_paid:
                    if line.is_skip:
                        amt += line.ins_interest
                    else:
                        amt += line.total_installment
            loan.paid_amount = amt

    def compute_installment(self):
        vals = []
        for i in range(0,self.term):
            date = self.start_date
            date = date+relativedelta(months=i)
            amount = self.loan_amount
            interest_amount = 0.0
            ins_interest_amount=0.0
            if self.is_apply_interest:
                amount = self.loan_amount
                interest_amount = (amount * self.term/12 * self.interest_rate)/100

                if self.interest_rate and self.loan_amount and self.interest_type == 'reduce':
                    amount = self.loan_amount - self.installment_amount * i
                    interest_amount = (amount * self.term / 12 * self.interest_rate) / 100
                ins_interest_amount = interest_amount / self.term
            vals.append((0, 0,{
                'name': 'INS - '+self.name + ' - '+str(i+1),
                'employee_id': self.employee_id and self.employee_id.id or False,
                'date': date,
                'amount': amount,
                'interest': interest_amount,
                'installment_amt': self.installment_amount,
                'ins_interest': ins_interest_amount,
            }))
        if self.installment_lines:
            for l in self.installment_lines:
                l.unlink()
        self.installment_lines=vals
        self.lone_report_state()

    @api.depends('paid_amount','loan_amount','interest_amount')
    def get_remaing_amount(self):
        for loan in self:
            remaining = (loan.loan_amount + loan.interest_amount) - loan.paid_amount
            loan.remaing_amount = remaining

    @api.depends('loan_amount','interest_rate','is_apply_interest')
    def get_interest_amount(self):
        for loan in self:
            amt = 0.0
            if loan.is_apply_interest:
                if loan.interest_rate and loan.loan_amount and loan.interest_type == 'liner':
                    loan.interest_amount = (loan.loan_amount * loan.term/12 * loan.interest_rate)/100
                if loan.interest_rate and loan.loan_amount and loan.interest_type == 'reduce':
                    loan.interest_amount = (loan.remaing_amount * loan.term/12 * loan.interest_rate)/100
                    for line in loan.installment_lines:
                        amt += line.ins_interest
            loan.interest_amount = amt

    # @api.depends('interest_amount')
    # def get_install_interest_amount(self):
    #     for loan in self:
    #         if loan.is_apply_interest:
    #             if loan.interest_amount and loan.term:
    #                 loan.ins_interest_amount = loan.interest_amount / loan.term

    @api.onchange('interest_type','interest_rate')
    def onchange_interest_rate_type(self):
        if self.interest_type and self.is_apply_interest:
            if self.interest_rate != self.loan_type_id.interest_rate:
                self.interest_rate = self.loan_type_id.interest_rate
            if self.interest_type != self.loan_type_id.interest_type:
                self.interest_type = self.loan_type_id.interest_type

    def get_loan_url(self):
        for loan in self:
            ir_param = self.env['ir.config_parameter'].sudo()
            base_url = ir_param.get_param('web.base.url')
            action_id = self.env.ref('pt_hr_dev_loan.action_employee_loan').id
            menu_id = self.env.ref('pt_hr_dev_loan.menu_employee_loan').id
            if base_url:
                base_url += '/web#id=%s&action=%s&model=%s&view_type=form&cids=&menu_id=%s' % (loan.id, action_id, 'employee.loan', menu_id)
            loan.loan_url = base_url

    @api.depends('term','loan_amount')
    def get_installment_amount(self):
        amount = 0
        for loan in self:
            if loan.loan_amount and loan.term:
                amount = loan.loan_amount / loan.term
            loan.installment_amount = amount

    @api.constrains('employee_id')
    def _check_loan(self):
        now = datetime.now()
        year = now.year
        s_date = str(year)+'-01-01'
        e_date = str(year)+'-12-01'
        
        loan_ids = self.search([('employee_id','=',self.employee_id.id),('date','<=',e_date),('date','>=',s_date)])
        loan = len(loan_ids)
        if loan > self.employee_id.loan_request:
            raise ValidationError("You can create maximum %s loan" % self.employee_id.loan_request)

    @api.constrains('loan_amount','term','loan_type_id','employee_id.loan_request')
    def _check_loan_amount_term(self):
        for loan in self:
            if loan.loan_amount <= 0:
                raise ValidationError("Loan Amount must be greater 0.00")
            elif loan.loan_amount > loan.loan_type_id.loan_limit:
                raise ValidationError("Your can apply only %s amount loan" % loan.loan_type_id.loan_limit)

            if loan.term <= 0:
                raise ValidationError("Loan Term must be greater 0.00")
            elif loan.term > loan.loan_type_id.loan_term:
                raise ValidationError("Loan Term Limit for Your loan is %s months" % loan.loan_type_id.loan_term)

    @api.onchange('loan_type_id')
    def _onchange_loan_type(self):
        if self.loan_type_id:
            if self.term == 0:
                self.term = self.loan_type_id.loan_term
            self.is_apply_interest = self.loan_type_id.is_apply_interest
            if self.is_apply_interest:
                self.interest_rate = self.loan_type_id.interest_rate
                self.interest_type = self.loan_type_id.interest_type
    
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            if self.employee_id.department_id:
                self.department_id = self.employee_id.department_id.id
            if self.employee_id.department_id:
                self.manager_id = self.department_id.manager_id.id
            if self.employee_id.job_id:
                self.job_id = self.employee_id.job_id.id

    def action_send_request(self):
        if not self.manager_id:
            raise ValidationError(_('Please Select Department manager'))
        
        self.state = 'request'
        if not self.installment_lines:
            self.compute_installment()
        if self.manager_id and self.manager_id.work_email:
            ir_model_data = self.env['ir.model.data']
            template_id = self.env.ref('pt_hr_dev_loan.dev_dep_manager_request')
            mtp = self.env['mail.template']
            template_id = mtp.browse(template_id.id)
            template_id.write({'email_to': self.manager_id.work_email})
            template_id.send_mail(self.ids[0], True)
        self.lone_report_state()

    def get_hr_manager_email(self):
        group_id = self.env.ref('hr.group_hr_manager').id
        group_ids = self.env['res.groups'].browse(group_id)
        email=''
        if group_ids:
            employee_ids = self.env['hr.employee'].search([('user_id', 'in', group_ids.users.ids)])

            for emp in employee_ids:
                if emp.work_email:
                    if email:
                        email = str(email) + ' , ' + str(emp.work_email)
                    else:
                        email = emp.work_email
        return email

    def dep_manager_approval_loan(self):
        self.state = 'dep_approval'
        email = self.get_hr_manager_email()
        if email:
            ir_model_data = self.env['ir.model.data']
            template_id = self.env.ref('pt_hr_dev_loan.dev_hr_manager_request')
            mtp = self.env['mail.template']
            template_id = mtp.browse(template_id.id)
            template_id.write({'email_to': email})
            template_id.send_mail(self.ids[0], True)

    def hr_manager_approval_loan(self):
        self.state = 'hr_approval'
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        self.hr_manager_id = employee_id and employee_id.id or False
        if self.employee_id.work_email and self.hr_manager_id:
            ir_model_data = self.env['ir.model.data']
            template_id = self.env.ref('pt_hr_dev_loan.hr_manager_confirm_loan')

            mtp = self.env['mail.template']
            template_id = mtp.browse(template_id.id)
            template_id.write({'email_to': self.employee_id.work_email})
            template_id.send_mail(self.ids[0], True)

    def dep_manager_reject_loan(self):
        self.state = 'reject'
        if self.employee_id.work_email:
            ir_model_data = self.env['ir.model.data']
            template_id = self.env.ref('pt_hr_dev_loan.dep_manager_reject_loan')

            mtp = self.env['mail.template']
            template_id = mtp.browse(template_id.id)
            template_id.write({'email_to': self.employee_id.work_email})
            template_id.send_mail(self.ids[0], True)

    def action_close_loan(self):
        self.state = 'close'
        if self.employee_id.work_email and self.hr_manager_id:
            ir_model_data = self.env['ir.model.data']
            template_id = self.env.ref('pt_hr_dev_loan.hr_manager_closed_loan')
            mtp = self.env['mail.template']
            template_id = mtp.browse(template_id.id)
            template_id.write({'email_to': self.employee_id.work_email})
            template_id.send_mail(self.ids[0], True)

    def hr_manager_reject_loan(self):
        self.state = 'reject'
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        self.hr_manager_id = employee_id and employee_id.id or False
        if self.employee_id.work_email and self.hr_manager_id:
            ir_model_data = self.env['ir.model.data']
            template_id = self.env.ref('pt_hr_dev_loan.hr_manager_reject_loan')

            mtp = self.env['mail.template']
            template_id = mtp.browse(template_id.id)
            template_id.write({'email_to': self.employee_id.work_email})
            template_id.send_mail(self.ids[0], True)

    def cancel_loan(self):
        self.state = 'cancel'

    def set_to_draft(self):
        self.state = 'draft'
        self.hr_manager_id = False

    def paid_loan(self):
        if not self.employee_id.address_home_id:
            raise ValidationError(_('Employee Private Address is not selected in Employee Form !!!'))
            
        self.state = 'financial_approval'
        vals={
            'date':self.date,
            'ref':self.name,
            'journal_id':self.loan_type_id.journal_id and self.loan_type_id.journal_id.id,
            'company_id':self.env.user.company_id.id
        }
        acc_move_id = self.env['account.move'].create(vals)
        if acc_move_id:
            lst = []
            val = (0,0,{
                            'account_id':self.loan_type_id and self.loan_type_id.loan_account.id,
                            'partner_id':self.employee_id.address_home_id and self.employee_id.address_home_id.id or False,
                            'name': self.name,
                            'debit': self.loan_amount or 0.0,
                            'move_id': acc_move_id.id,
                        })
            lst.append(val)

            if self.interest_amount:
                val = (0,0,{
                                'account_id':self.loan_type_id and self.loan_type_id.interest_account.id,
                                'partner_id':self.employee_id.address_home_id and self.employee_id.address_home_id.id or False,
                                'name': str(self.name)+' - '+'Interest',
                                'credit':self.interest_amount or 0.0,
                                'move_id': acc_move_id.id,
                            })
                lst.append(val)

            credit_account=False
            # base module code
            # if self.employee_id.address_home_id and self.employee_id.address_home_id.property_account_payable_id:
            #     credit_account = self.employee_id.address_home_id.property_account_payable_id.id or False

            credit_amount = self.loan_amount
            if self.interest_amount:
                credit_amount += self.interest_amount
            val = (0,0,{
                        'account_id': self.loan_type_id.payable_emp_account.id or False,
                        'partner_id':self.employee_id.address_home_id and self.employee_id.address_home_id.id or False,
                        'name': '/',
                        'credit': credit_amount or 0.0,
                        'move_id': acc_move_id.id,
                    })
            lst.append(val)
            acc_move_id.line_ids = lst
            self.move_id = acc_move_id.id
            for user in self.paid_by_ids:
                self.make_activity_user(user)

    def make_activity_user(self, user):
        date_deadline = fields.Date.today()
        note = _("Please Review Request")
        summary = _("Employee Loan")

        self.sudo().activity_schedule(
            'mail.mail_activity_data_todo', date_deadline,
            note=note,
            user_id=user.id,
            res_id=self.id,
            summary=summary
        )

    def loan_payment(self):
        for rec in self:
            return {
                'name': _('Payments'),
                'view_mode': 'form',
                'res_model': 'account.payment',
                'view_id': self.env.ref('account.view_account_payment_form').id,
                'type': 'ir.actions.act_window',
                'context': {'default_payment_type': 'outbound',
                            'default_partner_type': 'supplier',
                            'default_partner_id': rec.employee_id.address_home_id.id,
                            'default_date': rec.date,
                            'default_amount': rec.loan_amount,
                            'default_employee_loan_id': rec.id,
                            },
            }

    def view_journal_entry(self):
        if self.move_id:
            return {
                'view_mode': 'form',
                'res_id': self.move_id.id,
                'res_model': 'account.move',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
            }

    payments_count = fields.Integer(compute='get_payments_count')

    def view_payments(self):
        return {
            'name': _('Payments'),
            'domain': [('employee_loan_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'account.payment',
            'view_id': False,
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
        }

    def get_payments_count(self):
        count = self.env['account.payment'].search_count([('employee_loan_id', '=', self.id)])
        self.payments_count = count

    def action_done_loan(self):
        self.state = 'done'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('employee.loan') or '/'
        return super().create(vals_list)
        
    def copy(self, default=None):
        if default is None:
            default = {}
        default['name'] = '/'
        return super(employee_loan, self).copy(default=default)
    
    def unlink(self):
        for loan in self:
            if loan.state != 'draft':
                raise ValidationError(_('Loan delete in draft state only !!!'))
        return super(employee_loan,self).unlink()

    def action_view_loan_installment(self):
        action = self.env.ref('pt_hr_dev_loan.action_installment_line').read()[0]

        installment = self.mapped('installment_lines')
        if len(installment) > 1:
            action['domain'] = [('id', 'in', installment.ids)]
        elif installment:
            action['views'] = [(self.env.ref('pt_hr_dev_loan.view_loan_emi_form').id, 'form')]
            action['res_id'] = installment.id
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

class LoanReportState(models.Model):
    _name = 'lone.report.state'
    _description = 'Loan Report State'

    name = fields.Char()
    employee_loan_id = fields.Many2one("employee.loan")
    loan_line_id = fields.Many2one("installment.line")