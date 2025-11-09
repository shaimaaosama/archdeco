# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, exceptions
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo import tools, _


class HREndServiceBenefits(models.Model):
    _name = 'hr.end.service.benefit'
    _description = 'Employee End Of Service Benefits'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    # @api.constrains('total_taken_amount', 'amount')
    # def _check_amounts(self):
    #     for record in self:
    #         diff = record.total_deserved_amount - record.total_taken_amount
    #         if diff < record.amount:
    #             raise ValidationError('Your have exceed the residual amount')

    @api.constrains('date')
    def unique_end_service_benefit_date_per_employee(self):
        """Constraint to prevent create 2 end service benefits at the same day for them same employee"""
        for record in self:
            if record.date:
                end_service_benefit_ids = self.env['hr.end.service.benefit'].search(
                    [('employee_id', '=', record.employee_id.id), ('date', '=', record.date),
                     ('state', 'not in', ['cancel'])])
                if len(end_service_benefit_ids) > 1:
                    raise ValidationError(_('Employee has another end service benefit that date'))

    @api.constrains('total_deserved_amount')
    def _check_total_deserved_amount(self):
        for record in self:
            if record.total_deserved_amount == 0:
                raise ValidationError(record.end_service_benefit_type_id.zero_message)

    def _default_employee(self):
        """:returns current logged in employee using configured employee"""
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)

    @api.depends('hiring_date', 'date')
    def _compute_period(self):
        for record in self:
            if record.hiring_date:
                hiring_date = record.hiring_date
                period_days = relativedelta(record.date, hiring_date) + relativedelta(days=1)
                record.years = period_days.years
                record.months = period_days.months
                record.days = period_days.days
                period = period_days.years + (period_days.months / 12.0) + (period_days.days / 365.0)
                record.service_period = period

    @api.depends('employee_id', 'service_period', 'end_service_benefit_type_id', 'date',
                 'total_holiday_deserved_amount', 'type', 'payment_type', 'other_amount',
                 'employee_id.contract_id.eos_total_amount')
    def _compute_total_deserved_amount(self):
        for record in self:
            # if record.payment_type == 'wage_allowance' and record.end_service_benefit_type_id and record.type == 'ending_service':
            #     record.total_deserved_amount = record.employee_id.contract_id.eos_total_amount
            #     continue
            contract_id = self.env['hr.contract'].search(
                [('employee_id', '=', record.employee_id.id), ('state', '=', 'open')],
                limit=1, order='id desc')
            if contract_id:
                wage = contract_id.wage
                food = contract_id.food_allowance_val
                trans = contract_id.trans_allowance_val
                house = contract_id.house_allowance_val
                allowances = 0
                if record.payment_type == 'wage_allowance':
                    allowances = sum(contract_id.contract_allowances.mapped('amount'))
                total = 0.0
                service_period = record.years + (record.months / 12.0) + (record.days / 365.0)
                if record.end_service_benefit_type_id.deserved_after <= service_period:
                    residual = service_period
                    total_taken_years = 0
                    for line in record.end_service_benefit_type_id.line_ids:
                        if residual > line.deserved_for - total_taken_years:
                            total += line.deserved_months * (line.deserved_for - total_taken_years) * (
                                    wage + allowances + food + trans + house)
                            total_taken_years = line.deserved_for
                            residual = service_period - line.deserved_for
                        else:
                            total += line.deserved_months * residual * (wage + allowances + food + trans + house)
                            total_taken_years += residual
                            residual = 0.0
                other_amount = record.other_amount if record.type == 'ending_service' else 0
                # record.total_deserved_amount = total + (record.total_holiday_deserved_amount or 0) + other_amount
                record.total_deserved_amount = total
                if record.end_service_benefit_type_id.resignation_request:
                    service_period = record.years + (record.months / 12.0) + (record.days / 365.0)
                    for line in record.end_service_benefit_type_id.line_ids:
                        if service_period < line.deserved_for:
                            record.total_deserved_amount /= line.percentage_amount
                            break

    @api.depends('employee_id', 'holiday_line_ids', 'holiday_line_ids.remaining_leaves', 'type', 'payment_type')
    def _compute_total_holiday_deserved_amount(self):
        for record in self:
            total = 0.0
            if record.type == 'ending_service' or record.type == 'replacement':
                contract_id = self.env['hr.contract'].search(
                    [('employee_id', '=', record.employee_id.id), ('state', '=', 'open')],
                    limit=1, order='id desc')
                if contract_id:
                    wage = contract_id.wage
                    food = contract_id.food_allowance_val
                    trans = contract_id.trans_allowance_val
                    house = contract_id.house_allowance_val
                    allowances = 0
                    if record.payment_type == 'wage_allowance' and contract_id.contract_allowances:
                        allowances = sum(contract_id.contract_allowances.mapped('amount'))
                        # print("bbbbbbbbbbbb" ,allowances )
                    total = 0.0
                    for line in record.holiday_line_ids:
                        if line.pay:
                            total += line.remaining_leaves * ((wage + allowances + food + trans + house) / 30)
                            print("total" , total)
            record.total_holiday_deserved_amount = total

    @api.depends('employee_id', 'payslip_ids', 'payslip_ids.line_ids')
    def _compute_total_payslip_deserved_amount(self):
        payslip_total = 0
        for record in self:
            payslip_total += sum(
                line.total for line in record.payslip_ids.line_ids
                if line.salary_rule_id.code == 'NET'
            )
            record.total_payslip_deserved_amount = payslip_total


    @api.depends('employee_id')
    def _compute_total_taken_amount(self):
        for record in self:
            benefits_ids = self.env['hr.end.service.benefit'].search([
                ('employee_id', '=', record.employee_id.id),
                ('state', 'in', ['validated', 'paid']),
            ])
            sum = 0
            for benefits_id in benefits_ids:
                sum += benefits_id.amount
            record.total_taken_amount = sum

    @api.depends('total_deserved_amount', 'total_taken_amount')
    def _compute_available_amount(self):
        for record in self:
            record.available_amount = record.total_deserved_amount - record.total_taken_amount

    @api.depends('state')
    def _compute_payment_button_invisible(self):
        for record in self:
            record.payment_button_invisible = True
            if record.state != 'validated':
                record.payment_button_invisible = False
            if record.payment_id:
                record.payment_button_invisible = False

    @api.depends('total_deserved_amount', 'total_payslip_deserved_amount' , 'total_holiday_deserved_amount' ,
                 'last_month_worked' , 'other_allowance','ticket')
    def _compute_total_reward(self):
        for record in self:
            record.total_reward = (record.total_deserved_amount + record.total_payslip_deserved_amount +
                                   record.total_holiday_deserved_amount +record.last_month_worked +
                                   record.other_allowance + record.ticket)

    name = fields.Char(string='Reference', copy=False, default=_('New'),
                       tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('send_submit', 'Sent'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('pay_progress', 'Payment in progress'),
        ('journal_draft', 'Journal Entry Draft'),
        ('post', 'Posted'),
        ('done', 'Done'),
        ('paid', 'Payed'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', track_visibility='onchange', copy=False)
    employee_id = fields.Many2one('hr.employee', string='Employee', index=True, readonly=True,
                                  states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
                                  tracking=True)
    department_id = fields.Many2one(comodel_name="hr.department", string="Department",
                                    related='employee_id.department_id', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    date = fields.Date(string="Date", default=datetime.now().strftime('%Y-%m-%d'), tracking=True,
                       copy=False)
    type = fields.Selection(string="Reward Type",
                            selection=[('replacement', 'Replacement'), ('ending_service', 'Ending Service'), ],
                            default='ending_service', )
    payment_type = fields.Selection(string="Payment Type",
                                    selection=[('wage', 'Wage'), ('wage_allowance', 'Wage + Allowances'), ],
                                    default='wage_allowance', required=True)
    end_service_benefit_type_id = fields.Many2one(comodel_name="hr.end.service.benefit.type", string="ES Reason", )
    hiring_date = fields.Date(string="Hiring Date", related='employee_id.hiring_date', store=True)
    years = fields.Integer(string="Years", compute=_compute_period, store=True)
    months = fields.Integer(string="Months", compute=_compute_period, store=True)
    days = fields.Integer(string="Days", compute=_compute_period, store=True)
    service_period = fields.Float(string="Service Period In Years", compute=_compute_period, store=True)
    notes = fields.Text(string="Notes", tracking=True)
    company_id = fields.Many2one('res.company', string='Company', related='employee_id.company_id', store=True)
    total_holiday_deserved_amount = fields.Float(string="Total Time Off Deserved Amount",
                                                 compute=_compute_total_holiday_deserved_amount, store=True)
    total_payslip_deserved_amount = fields.Float(string="Total Payslip Deserved Amount",
                                                 compute=_compute_total_payslip_deserved_amount, store=True)
    last_month_worked = fields.Float('Last Month Worked Days Amount' , compute='_compute_last_month_worked' , store=True)
    other_amount = fields.Float(string="Other Amount")
    total_deserved_amount = fields.Float(string="ESR Deserved Amount", compute=_compute_total_deserved_amount,
                                         store=True)
    total_taken_amount = fields.Float(string="Previously ESR Disbursed Amount", compute=_compute_total_taken_amount,
                                      store=True)
    available_amount = fields.Float(string="Available to Disbursed", compute=_compute_available_amount, store=True)
    deduction_loan = fields.Float(compute='_compute_deduction_loan')
    other_deduction = fields.Float(compute='_compute_other_deduction')
    other_allowance = fields.Float(compute='_compute_other_allowance')
    # /////////////////////////////////////////////////////////////////////
    ticket = fields.Float(compute='_compute_ticket')
    # ///////////////////////////////////////////////////////////////////
    amount = fields.Float(string="Reward Requested Amount", required=False, compute='_compute_amount' )
    payment_id = fields.Many2one(comodel_name="account.payment", string="Reward Payment", copy=False, )
    payslip_payment_id = fields.Many2one(comodel_name="account.payment", string="Payslip Payment", copy=False, )
    account_move_id = fields.Many2one(comodel_name="account.move", string="Expense entry", copy=False, )
    payment_button_invisible = fields.Boolean(compute=_compute_payment_button_invisible)
    holiday_line_ids = fields.One2many('hr.end.benefit.holiday.line', 'reward_id', string="Holiday Lines",
                                       compute="_compute_holiday_lines", store=True)#compute="_compute_holiday_lines",
    payslip_id = fields.Many2one(comodel_name="hr.payslip", string="Payslip")
    payslip_ids = fields.Many2many(
        comodel_name="hr.payslip", string="Payslips",
        domain="[('state', '=', 'done'), ('employee_id', '=', employee_id)]",
        options="{'no_create': True}",
        readonly="state != 'draft'"
    )
    pt_cash_account_id = fields.Many2one(related='employee_id.pt_cash_account_id')
    pt_cash_balance = fields.Float(string='Ptty Cash Amount', compute="_compute_pt_cash_balance", store=True)
    days_number = fields.Float(string="Last Month Worked Days Number", default=0)
    total_reward = fields.Float(string="Total ESR, Payslip,Time Off and Ticket", compute=_compute_total_reward, store=True)

    vacation_settlement_id = fields.Many2one(
        'employee.vacation.settlement',
        string="Vacation Settlement"
    )


    sent_date = fields.Date(string="Send Date")
    submit_date = fields.Date(string="Submit Date")
    payment_date = fields.Date(string="Payment Date")

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            # ==========================
            # 1) Load Payslips
            # ==========================
            payslips = self.env['hr.payslip'].search([
                ('state', '=', 'done'),
                ('employee_id', '=', self.employee_id.id)
            ])
            self.payslip_ids = payslips
    @api.depends('employee_id', 'type')
    def _compute_holiday_lines(self):
        for record in self:
            if record.type in ['ending_service', 'replacement'] and record.employee_id:
                # find validated allocations for this employee
                allocation_ids = self.env['hr.leave.allocation'].search([
                    ('employee_id', '=', record.employee_id.id),
                    ('state', 'not in', ['draft', 'cancel', 'refuse'])
                ])
                holiday_status_ids = allocation_ids.mapped('holiday_status_id')

                # build fresh lines (one per holiday type)
                lines_ids = []
                for holiday_status in holiday_status_ids:
                    lines_ids.append((0, 0, {
                        'holiday_id': holiday_status.id,
                        'remaining_leaves': 0.0,  # will be recomputed by holiday line compute
                        'reward_id': record.id,
                        'pay': True,
                    }))

                # reset old lines, then set new ones
                record.holiday_line_ids = [(5, 0, 0)] + lines_ids
            else:
                # not ending_service/replacement: clear the lines
                record.holiday_line_ids = [(5, 0, 0)]

    # @api.depends('employee_id', 'type')
    # def _compute_holiday_lines(self):
    #     for record in self:
    #         if record.type == 'ending_service' or record.type == 'replacement' :
    #             record.holiday_line_ids = [(5, 0, 0)]  # 🔥 Clear existing lines
    #
    #             allocation_ids = self.env['hr.leave.allocation'].search([
    #                 ('employee_id', '=', record.employee_id.id),
    #                 ('state', 'not in', ['draft', 'cancel', 'refuse'])
    #             ])
    #
    #             holiday_status_ids = allocation_ids.mapped('holiday_status_id')
    #             employee = record.employee_id
    #             lines_ids = []
    #
    #             if employee and holiday_status_ids:
    #                 employee_record = self.env['hr.employee'].browse(employee.id)
    #                 allocation_data = holiday_status_ids.get_employees_days([employee.id])
    #
    #                 if allocation_data and employee in allocation_data:
    #                     for data_tuple in allocation_data[employee]:
    #                         holiday_name, leave_data, _, holiday_status_id = data_tuple
    #                         remaining_leaves = leave_data.get('remaining_leaves', 0)
    #
    #                         # ✅ Convert Units if Needed
    #                         holiday_status = self.env['hr.leave.type'].browse(holiday_status_id)
    #                         if holiday_status.request_unit == 'hour':
    #                             remaining_leaves /= (employee.company_id.number_of_hours_per_day or 8)
    #                         elif holiday_status.request_unit == 'half_day':
    #                             remaining_leaves /= 2
    #
    #                         lines_ids.append((0, 0, {
    #                             'holiday_id': holiday_status_id,
    #                             'remaining_leaves': remaining_leaves,
    #                             'reward_id': record.id,  # Ensure One2many relation is set
    #                         }))
    #
    #             record.holiday_line_ids = lines_ids

    @api.depends('employee_id')
    def _compute_pt_cash_balance(self):
        for rec in self:
            balance = 0
            if rec.pt_cash_account_id and rec.employee_id.address_home_id:
                move_lines = self.env['account.move.line'].search([
                    ('account_id', '=', rec.pt_cash_account_id.id),
                    ('partner_id', '=', rec.employee_id.address_home_id.id),
                    ("parent_state", "=", "posted")]
                )
                for move_line in move_lines:
                    balance += move_line.balance
            rec.pt_cash_balance = balance

    @api.depends('employee_id','days_number')
    def _compute_last_month_worked(self):
        for record in self:
            total = 0.0

            contract_id = self.env['hr.contract'].search(
                    [('employee_id', '=', record.employee_id.id), ('state', '=', 'open')],
                    limit=1, order='id desc')
            if contract_id:
                    wage = contract_id.wage
                    food = contract_id.food_allowance_val
                    trans = contract_id.trans_allowance_val
                    house = contract_id.house_allowance_val
                    allowances = contract_id.other_allowance_val
                    total += record.days_number * ((wage + allowances + food + trans + house) / 30)
                    print("totalllllllllllllllll", total)
            record.last_month_worked = total

    @api.depends('allows_ids' , 'allows_ids.other_allowances')
    def _compute_other_allowance(self):
        for rec in self:
            rec.other_allowance = sum(rec.allows_ids.mapped('other_allowances'))
    # /////////////////////////////////////////////////////////
    @api.depends('tick_ids' , 'tick_ids.ticket')
    def _compute_ticket(self):
        for rec in self:
            rec.ticket = sum(rec.tick_ids.mapped('ticket'))
    # ////////////////////////////////////////////////////////////////////////

    @api.depends('employee_id')
    def _compute_deduction_loan(self):
        for record in self:
            if not record.employee_id:
                record.deduction_loan = 0.0
                continue

            employee_loans = self.env['employee.loan'].search([
                ('employee_id', '=', record.employee_id.id),
            ])

            total_deduction = sum(employee_loans.mapped('remaing_amount'))


            record.deduction_loan = total_deduction

    @api.depends('deduct_ids' , 'deduct_ids.detuction')
    def _compute_other_deduction(self):
        for rec in self:
            rec.other_deduction = sum(rec.deduct_ids.mapped('detuction'))

    @api.depends('deduction_loan' , 'other_deduction' , 'total_reward')
    def _compute_amount(self):
        for rec in self:
            # rec.pt_cash_balance = -1 * rec.pt_cash_balance
            rec.amount = rec.total_reward - rec.deduction_loan - rec.other_deduction + rec.pt_cash_balance



    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('You can only delete draft end service benefits'))
        res = super(HREndServiceBenefits, self).unlink()
        return res

    @api.model
    def create(self, vals):
        res = super().create(vals)
        for record in res:
            vacation_settlement = self.env['employee.vacation.settlement'].search(
                [('employee_id', '=', record.employee_id.id), ('vacation_end_service', '=', True)], limit=1)
            if vacation_settlement:
                vacation_settlement.vacation_source = record.name  # Update the field properly
        return res

    # def action_submit(self):
    #     for record in self:
    #         group_manager = self.env.ref('hr.group_hr_manager')
    #         recipient_partners = []
    #         mail_server = self.env['ir.mail_server'].sudo().search([], order="sequence asc", limit=1)
    #         for recipient in group_manager[0].users:
    #             recipient_partners.append(
    #                 (4, recipient.partner_id.id)
    #             )
    #         template = False
    #         if recipient_partners and mail_server:
    #             template = self.env['ir.model.data'].get_object('hr_end_service_benefits',
    #                                                             'email_es_request_submission')
    #
    #         if template:
    #             mail_template = self.env['mail.template'].browse(template.id)
    #             mail_id = mail_template.send_mail(record.id)
    #             mail = self.env['mail.mail'].browse([mail_id])
    #             mail.recipient_ids = recipient_partners
    #         if record.amount <= 0:
    #             raise ValidationError(_('You can not confirm rewards with amount of zero'))
    #         SequenceObj = self.env['ir.sequence']
    #         number = SequenceObj.next_by_code('hr.end.service.benefit')
    #         record.name = number
    #         vacation_settlement = self.env['employee.vacation.settlement'].search(
    #             [('employee_id', '=', record.employee_id.id) , ('vacation_end_service' , '=' , True)], limit=1)
    #         if vacation_settlement:
    #             vacation_settlement.vacation_source = record.name
    #
    #
    #     record.write({'state': 'confirmed', 'name': number})

    # def action_validate(self):
    #     for record in self:
    #         group_manager = self.env.ref('account.group_account_manager')
    #         recipient_partners = []
    #         mail_server = self.env['ir.mail_server'].sudo().search([], order="sequence asc", limit=1)
    #         for recipient in group_manager[0].users:
    #             recipient_partners.append(
    #                 (4, recipient.partner_id.id)
    #             )
    #         template = False
    #         if recipient_partners and mail_server:
    #             template = self.env['ir.model.data'].get_object('hr_end_service_benefits',
    #                                                             'email_es_request_payment_request')
    #         if template:
    #             mail_template = self.env['mail.template'].browse(template.id)
    #             mail_id = mail_template.send_mail(record.id)
    #             mail = self.env['mail.mail'].browse([mail_id])
    #             mail.recipient_ids = recipient_partners
    #
    #         record.write({'state': 'validated'})
    #         if record.type == 'ending_service' or record.type == 'replacement':
    #             record.employee_id.toggle_active()
    #             contract_ids = self.env['hr.contract'].search(
    #                 [('employee_id', '=', record.employee_id.id), ('state', '=', 'open')],
    #                 order='id desc')
    #             for contract_id in contract_ids:
    #                 contract_id.state = 'cancel'

    def action_draft(self):
        for record in self:
            record.write({'state': 'draft'})
            if record.payment_id:
                record.payment_id.action_draft()
    def action_send_to_submit(self):
        for record in self:
            record.sent_date = fields.Datetime.now()
            record.write({'state': 'send_submit'})


    # def action_cancel(self):
    #     for record in self:
    #         record.write({'state': 'cancel'})
    #         if record.payment_id:
    #             record.payment_id.cancel()
    #         if record.account_move_id:
    #             record.account_move_id.reverse_moves(record.account_move_id.date,
    #                                                  record.account_move_id.journal_id or False)

    def action_sheet_move_create(self):
        for rec in self:
            # Access the hr.benefit.settlement record related to the current hr.end.service.benefit record
            settlement = self.env['hr.benefit.settlement'].search([('request_id', '=', rec.id)], limit=1)

            if settlement and settlement.request_id.account_move_id and settlement.request_id.account_move_id.state == 'draft':
                # Post the draft journal entry
                settlement.request_id.account_move_id.action_post()
                rec.write({'state': 'post'})
                rec.message_post(body=_("Journal entry has been successfully posted."))
                print("Draft journal entry has been posted.")
            else:
                raise exceptions.ValidationError(
                    _("No draft journal entry found or the entry is already posted. Please create the draft entry first.")
                )

    account_id = fields.Many2one(
        'account.account',
        compute='_compute_account_id',
        store=True,
        readonly=False,
        precompute=True,
        string='Account',
        help="An expense account is expected"
    )



    @api.model
    def _default_journal_id(self):
        """ The journal is determining the company of the accounting entries generated from expense. We need to force journal company and expense sheet company to be the same. """
        journal = self.env['account.journal'].search([('is_vacation', '=', True)], limit=1)
        return journal.id

    journal_id = fields.Many2one('account.journal', string='vacation Journal', domain="[('is_vacation', '=', True)]",
                                 default=_default_journal_id, help="The journal used when the expense is done.")

    def action_sheet_move_create_draft(self):
        for rec in self:
            # Pass the necessary data to the wizard (without storing the Many2one reference)
            wizard = self.env['hr.benefit.settlement'].create({
                'request_id': rec.id,
            })
            wizard.settle_employee_reward_emp()
            rec.write({'state': 'journal_draft'})
            print("Settlement processed successfully")



    def action_reset_to_draft(self):
        return self.write({'state': 'draft'})

    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_submit(self):
        for record in self:
            record.write({'state': 'submit'})
            record.submit_date = fields.Datetime.now()

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_approve(self):
        self.write({'state': 'approve'})

    def action_payment_in_progress(self):
        for record in self:
            record.write({'state': 'pay_progress'})
            record.payment_date = fields.Datetime.now()

    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        There can be more than one bank_account_id in the expense sheet when registering payment for multiple expenses.
        The default_partner_bank_id is set only if there is one available, if more than one the field is left empty.
        :return: An action opening the account.payment.register wizard.
        '''
        AccountMove = self.env['account.move'].search([('ref', '=', self.name)], limit=1)

        self.write({'state': 'paid'})
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

    def action_open_account_move(self):
        self.ensure_one()

        # Find the settlement record related to the current record
        settlement_record = self.env['hr.benefit.settlement'].search([('request_id', '=', self.id)], limit=1)

        if settlement_record:
            AccountMove = self.account_move_id
            return {
                'name': AccountMove.name,
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'views': [[False, "form"]],
                'res_model': 'account.move',
                'res_id': AccountMove.id,
            }
        else:
            raise exceptions.UserError(_("No journal entry is linked to this record."))

    allows_ids = fields.One2many(comodel_name='employee.vacation.settlement.allowance', inverse_name='service_id', string="Allowances" , store=True)
    deduct_ids = fields.One2many(comodel_name='employee.vacation.settlement.detuction', inverse_name='service_id', string="Deduction" , store=True)
    tick_ids = fields.One2many(
        'employee.vacation.settlement.ticket',
        'service_id',
        string="Tickets",
        compute='_compute_tick_ids',
        store=True
    )

    @api.depends('employee_id', 'type')
    def _compute_tick_ids(self):
        """Auto-fill ticket lines based on employee's active contract and tickets."""
        for record in self:
            if record.employee_id and record.type in ['ending_service', 'replacement']:
                employee = record.employee_id
                lines = []

                # Find active contract
                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'open')
                ], limit=1)

                if contract:
                    # Find ticket lines (employee + followers)
                    ticket_lines = self.env['gs.tickets.line'].search([
                        ('contract_id', '=', contract.id),
                        ('type', 'in', ['employee', 'follower'])
                    ])

                    for t in ticket_lines:
                        lines.append((0, 0, {
                            'type_ticket': self.env['type.allowances'].search([
                                ('type', '=', 'ticket')
                            ], limit=1).id,
                            'ticket': t.ticket_fare,
                            'ticket_note': f"{t.name or ''} - {t.type.title()} Ticket",
                            'currency_id': t.contract_id.company_id.currency_id.id,
                            'service_id': record.id,
                        }))

                # reset old ticket lines and set new ones
                record.tick_ids = [(5, 0, 0)] + lines

            else:
                # Clear lines if no employee or not ending service
                record.tick_ids = [(5, 0, 0)]

# /////////////////////////////////////////////////////////
class EmployeeVacationSettlementTicket(models.Model):
    _inherit = 'employee.vacation.settlement.ticket'
    _description = 'Employee Vacation Settlement Ticket'

    service_id = fields.Many2one('hr.end.service.benefit', string='Tickets End Service', ondelete='cascade')

# //////////////////////////////////////////////////////////


class EmployeeVacationSettlementDetuction(models.Model):
    _inherit = 'employee.vacation.settlement.detuction'
    _description = 'Employee Vacation Settlement Deduction'

    service_id = fields.Many2one('hr.end.service.benefit', string='Deductions End Service', ondelete='cascade')

class EmployeeVacationSettlementAllowance(models.Model):
    _inherit = 'employee.vacation.settlement.allowance'
    _description = 'Employee Vacation Settlement Deduction'

    service_id = fields.Many2one('hr.end.service.benefit', string='Allowances End Service', ondelete='cascade')



class HolidaysReward(models.Model):
    _name = 'hr.end.benefit.holiday.line'
    _description = 'Holiday Reward'

    def get_remaining_leaves(self, employee, leave_type=None):
        """Return remaining leaves (days) for employee, optionally per leave type"""
        allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate')
        ])
        remaining = 0
        for alloc in allocations:
            if leave_type and alloc.holiday_status_id != leave_type:
                continue
            remaining += alloc.number_of_days_display - alloc.leaves_taken
        return remaining

    # ----------------------------------------------------------------
    # COMPUTE
    # ----------------------------------------------------------------
    @api.depends('employee_id', 'holiday_id', 'reward_id')
    def _compute_leaves(self):
        for record in self:
            record.remaining_leaves = 0

            if not record.employee_id or not record.holiday_id:
                continue

            # Find employee's open contract
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', record.employee_id.id),
                ('state', '=', 'open')
            ], limit=1)

            daily_wage = contract.vacation_total_amount / 30 if contract and contract.vacation_total_amount else 0

            # Find allocations of this holiday type
            allocations = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', record.employee_id.id),
                ('holiday_status_id', '=', record.holiday_id.id),
                ('state', '=', 'validate')
            ])

            total_allocated = sum(a.number_of_days_display for a in allocations)

            # Leaves already taken
            taken = self.env['hr.leave'].search([
                ('employee_id', '=', record.employee_id.id),
                ('holiday_status_id', '=', record.holiday_id.id),
                ('state', '=', 'validate')
            ])
            total_taken = sum(t.number_of_days for t in taken)

            # Remaining days
            remaining = total_allocated - total_taken
            if remaining < 0:
                remaining = 0

            # Adjust for hours or half-days
            if record.holiday_id.request_unit == 'hour':
                remaining = remaining / (record.employee_id.company_id.number_of_hours_per_day or 8)
            elif record.holiday_id.request_unit == 'half_day':
                remaining = remaining / 2

            record.remaining_leaves = remaining

    holiday_id = fields.Many2one(comodel_name="hr.leave.type", string="Holiday", required=False)
    reward_id = fields.Many2one(comodel_name="hr.end.service.benefit")
    employee_id = fields.Many2one(comodel_name="hr.employee", related='reward_id.employee_id')
    remaining_leaves = fields.Float(string="Remaining Leaves", compute='_compute_leaves' , store=True)
    pay = fields.Boolean(string="Pay As Reward")
