# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class GsPenaltiesAwards(models.Model):
    _name = 'gs.penalties.awards'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Penalties & Awards'
    _rec_name = 'sequence_penalties_awards'

    def get_type_state(self):
        state = {'deduction': 'Deduction',
                 'award': 'Award',}
        return state[self.type]
    company_id = fields.Many2one('res.company',default=lambda self:self.env.company)
    name = fields.Char()
    employee_id = fields.Many2one('hr.employee', string="Employee Name",)
    date = fields.Date(string='Date',)
    number_of_days = fields.Integer(string='Number Of Days', )
    type = fields.Selection(string='Type', selection=[('deduction', 'Deduction'), ('award', 'Award'), ],)
    penalties_awards_id = fields.Many2one('gs.penalties.awards.setting', string='Penalties & Awards ', required=False)
    amount = fields.Float(string='Amount', )
    note = fields.Char(string='Reason', )
    is_attachment = fields.Boolean(string="is Attachment?")
    attachment_ids = fields.Many2many('ir.attachment', 'gs_attachment_rel01', 'gs_template_id001', 'gs_attachment_id001' , 'Attachments',)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('paid', 'Paid'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', tracking=True, copy=False, )
    dedication_month = fields.Date(string='Payment Due Date',)

    is_type_fixed = fields.Boolean(string='Is Fixed Amount?', required=False)
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    is_send_by_email = fields.Boolean()
    registration_number2 = fields.Char( related='employee_id.registration_number2',store=True,string='Employee Code')
    analytic_account_id = fields.Many2one('account.analytic.account',related='employee_id.contract_id.analytic_account_id', store=True, string='الفرع')
    department_manager_id = fields.Many2one('hr.employee',string="المدير القسم", related='employee_id.department_id.manager_id',store=True)
    manager_id = fields.Many2one('hr.employee',related='employee_id.parent_id',store=True, string='المدير المباشر')
    penalty_number = fields.Char('رقم المخالفه')
    number_of_penalty_repeat = fields.Integer('عدد تكرار المخالفه')
    penalty_date = fields.Date('تاريخ المخالفه')
    company_id = fields.Many2one('res.company',default=lambda self:self.env.company, string='الشركه')
    penalty_labour = fields.Boolean(related='penalties_awards_id.penalty_labour')
    country_labour = fields.Boolean(related='penalties_awards_id.country_labour')
    penalty_employee = fields.Boolean(related='penalties_awards_id.penalty_employee')
    description = fields.Char('الوصف')
    penalty_description = fields.Char('وصف المخالفه')
    penalty_note = fields.Char('ملاحظات المراقب')
    penalty_items = fields.Char('بندالمخالفات')
    penalty_num_close= fields.Char('عدد ايام الاغلاق')
    penalty = fields.Char('المخالفه')
    refused_option = fields.Selection([
        ('done', 'تم'),
        ('not_done', 'لم يتم'),
    ],string='الاعتراض')
    refused_state = fields.Selection([
        ('done', 'مقبول'),
        ('not_done', 'مرفوض'),
        ('load', 'تحت الاجراء'),
    ], string=' حاله الاعتراض')
    refused_date = fields.Date('تاريخ الاعتراض')
    last_refused_date = fields.Date('تاريخ اخر موعد لاعتراض')
    settlement_option = fields.Selection([
        ('done', 'تم'),
        ('not_done', 'لم يتم'),
    ],string='التسويه')
    refused_number = fields.Char('رقم الاعتراض')
    refused_note = fields.Char('نص الاعتراض')
    operation_details = fields.Char('اجراءات الرفع للمحكمه')
    area_name = fields.Char('اسم البلديه')
    penalty_num_repeat = fields.Char('عدد مرات تكرار المخالفه')
    penalty_build_num = fields.Char('عدد وحدات المخالفه')
    penalty_update = fields.Char('تصحيح المخالفه')
    license_number = fields.Char('رقم الرخصه')
    payment_number = fields.Char('رقم السداد')
    penalty_amount = fields.Char('قيمه المخالفه')
    settlement_number = fields.Char('رقم التسويه')
    operation = fields.Char('الاجراءات')
    operation_update = fields.Char('الجزاء المتخذ حيال المخالفه')
    location = fields.Char('الموقع')
    payment = fields.Selection([
        ('done', 'تم'),
        ('not_done', 'لم يتم'),
    ], string='الدفع')
    payment_state = fields.Selection([
        ('done', 'سدد'),
        ('not_done', 'غير مسدد'),
    ], string='حاله الدفع')
    penalty_area_number = fields.Char('رقم مخالفه البلديه')
    payment_operation =  fields.Selection([
        ('done', 'نعم'),
        ('not_done', 'لا'),
    ], string='هل تم حسم المبلغ بالكامل')
    pa_installment_ids = fields.One2many('gs.penalties.awards.installment', 'penalties_awards_id',
                                         string='Installments', )
    installment_count = fields.Integer(compute='get_interest_count')
    paid_amount = fields.Float('Paid Amount', compute='get_paid_amount', store=True)
    remaining_amount = fields.Float('Remaining amount', compute='get_paid_amount', store=True)
    term = fields.Integer('Term', required=True)
    start_date = fields.Date('Start Date', default=fields.Date.today(), required=True)
    end_date = fields.Date('End Date', compute='_get_end_date')
    installment_amount = fields.Float('Installment Amount', required=False, compute='get_installment_amount',
                                      store=True)

    paid_by = fields.Selection([
        ('employee', 'Employee'),
        ('company', 'Company'),
    ], string='Paid by', default='employee')
    journal_entry_id = fields.Many2one('account.move', string="Journal Entries")

    def action_open_journal_entries(self):
        self.ensure_one()
        if not self.journal_entry_id:
            raise UserError(_("No journal entries linked."))
        return {
            'name': _('Journal Entry'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.journal_entry_id.id,
            'target': 'current',
        }

    @api.depends('pa_installment_ids')
    def get_interest_count(self):
        for loan in self:
            count = 0
            if loan.pa_installment_ids:
                count = len(loan.pa_installment_ids)
            loan.installment_count = count

    @api.depends('term', 'amount')
    def get_installment_amount(self):
        amount = 0
        for loan in self:
            if loan.amount and loan.term:
                amount = loan.amount / loan.term
            loan.installment_amount = amount

    @api.depends('pa_installment_ids', 'pa_installment_ids.is_paid')
    def get_paid_amount(self):
        for loan in self:
            amt = 0
            rem = 0
            for line in loan.pa_installment_ids:
                if line.is_paid:
                    if line.is_skip:
                        amt += line.ins_interest
                    else:
                        amt += line.total_installment
                else:
                    if line.is_skip:
                        rem += line.ins_interest
                    else:
                        rem += line.total_installment
            loan.paid_amount = amt
            loan.remaining_amount = rem

    @api.depends('start_date', 'term')
    def _get_end_date(self):
        for loan in self:
            end_date = False
            if loan.start_date and loan.term:
                start_date = self.start_date
                end_date = start_date + relativedelta(months=self.term)
            loan.end_date = end_date

    def compute_installment(self):
        vals = []
        for i in range(0, self.term):
            date = self.start_date
            date = date + relativedelta(months=i)
            amount = self.amount
            vals.append((0, 0, {
                'name': 'INS - ' + self.sequence_penalties_awards + ' - ' + str(i + 1),
                'employee_id': self.employee_id and self.employee_id.id or False,
                'date': date,
                'amount': amount,
                'installment_amt': self.installment_amount,
            }))
        if self.pa_installment_ids:
            for l in self.pa_installment_ids:
                l.unlink()
        self.pa_installment_ids = vals

    def unlink(self):
        for asset in self:
            if asset.sequence_penalties_awards != _('New'):
                raise UserError(_('You cannot delete a Penalties & Awards that is in %s state.') % (asset.state,))
        return super(GsPenaltiesAwards, self).unlink()

    def action_reset_to_draft(self):
        self.is_send_by_email = False
        return self.write({'state': 'draft'})

    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_submit(self):
        if self.sequence_penalties_awards == _('New'):
            self.sequence_penalties_awards = self.env['ir.sequence'].next_by_code('serial_for_penalties_awards') or _('New')
        self.write({'state': 'submit'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_approve(self):
        self.write({'state': 'approve'})

    def action_paid(self):
        self.write({'state': 'paid'})

    # _sql_constraints = [
    #     ('payment', 'unique (payment_number)', 'رقم السداد موجود بالفعل ')
    # ]
    @api.constrains('payment_number')
    def _onchange_payment_number(self):
        for record in self:
            if record.payment_number:
                payment = self.search([('payment_number', '=', record.payment_number)])
                if len(payment) > 1:
                    raise ValidationError('رقم السداد موجود بالفعل')


    recipient_users = fields.Text()

    def send_template_email(self, users, template):
        recipient_users = []
        if users.work_email not in recipient_users:
            recipient_users.append(users.work_email)

        recipient_users = '[%s]' % ', '.join(map(str, recipient_users))
        self.recipient_users = recipient_users

        template_id = template
        template = self.env['mail.template'].browse(template_id)
        template.send_mail(self.id, force_send=True)

    # @api.model
    # def create(self, vals):
    #     if vals.get('sequence_penalties_awards', _('New')) == _('New'):
    #         vals['sequence_penalties_awards'] = self.env['ir.sequence'].next_by_code(
    #             'serial_for_penalties_awards') or _('New')
    #
    #     result = super(GsPenaltiesAwards, self).create(vals)
    #     return result

    sequence_penalties_awards = fields.Char(string='Seq', required=True, copy=False, readonly=True,
                                          index=True, default=lambda self: _('New'))

    @api.onchange('type', 'number_of_days')
    def domain_penalties_awards_id(self):
        return {'domain': {'penalties_awards_id': [('type', '=', self.type)]}}

    @api.onchange('number_of_days', 'penalties_awards_id')
    def _onchange_number_of_days(self):
        for rec in self:
            sum_amount = 0
            if rec.penalties_awards_id.is_type_fixed:
                rec.is_type_fixed = True
            else:
                rec.is_type_fixed = False
                if rec.number_of_days:
                    contract = self.env['hr.contract'].search([('state', '=', 'open'), ('employee_id', '=', rec.employee_id.id)], limit=1)
                    for line in rec.penalties_awards_id.base_amount_ids:
                        if contract._fields['house_allowance_val'].string == line.name:
                            sum_amount += contract.house_allowance_val
                        if contract._fields['trans_allowance_val'].string == line.name:
                            sum_amount += contract.trans_allowance_val
                        if contract._fields['wage'].string == line.name:
                            sum_amount += contract.wage
                        for allowances in contract.contract_allowances:
                            if allowances.allowance_id.name == line.name:
                                sum_amount += allowances.amount
                    rec.amount = (sum_amount / rec.penalties_awards_id.base_num) * rec.number_of_days

#     /////////////////////////////////////////////////
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        domain="[('type', 'in', ('bank', 'cash'))]",
        required=False
    )

    draft_journal_entry_id = fields.Many2one(
        'account.move', string="Draft Journal Entry"
    )
    draft_journal_entry_state = fields.Selection(
        related="draft_journal_entry_id.state",
        string="Journal Entry State",
        store=True,
        readonly=True
    )

    def action_open_draft_journal_entry(self):
        self.ensure_one()
        if not self.draft_journal_entry_id:
            raise UserError(_("No Draft Journal Entry linked."))
        return {
            'name': _('Draft Journal Entry'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.draft_journal_entry_id.id,
            'target': 'current',
        }

    def action_create_draft_journal_entry(self):
        """Create Draft Journal Entry for Penalties/Awards"""
        move_obj = self.env['account.move']
        for rec in self:
            if rec.draft_journal_entry_id:
                continue  # already exists
            partner = rec.employee_id.address_home_id  # employee’s private address (res.partner)

            move_vals = {
                'move_type': 'entry',
                'journal_id': rec.env['account.journal'].search([('is_penalties_journal', '=', True)], limit=1).id,
                'date': fields.Date.today(),
                'ref': f"{rec.penalties_awards_id.name or ''} / {rec.penalty_number or ''}",
                'line_ids': [],
                'analytic_distribution': rec.analytic_account_id and {rec.analytic_account_id.id: 100} or False,
                'partner_id': partner.id if partner else False,

            }
            debit_account = rec.penalties_awards_id.account_debit_id
            credit_account = rec.penalties_awards_id.account_credit_id

            # debit line
            debit_line = {
                'account_id': debit_account.id,
                'debit': rec.amount,
                'credit': 0.0,
                'partner_id': partner.id if partner else False,
                'analytic_distribution': rec.analytic_account_id and {rec.analytic_account_id.id: 100} or False,
                'name': f"{rec.penalties_awards_id.name or ''} - {rec.penalty_number or ''}",
            }
            # credit line
            credit_line = {
                'account_id': credit_account.id,
                'debit': 0.0,
                'credit': rec.amount,
                'partner_id': partner.id if partner else False,
                'analytic_distribution': rec.analytic_account_id and {rec.analytic_account_id.id: 100} or False,
                'name': f"{rec.penalties_awards_id.name or ''} - {rec.penalty_number or ''}",
            }

            move_vals['line_ids'] = [(0, 0, debit_line), (0, 0, credit_line)]

            move = move_obj.create(move_vals)
            rec.draft_journal_entry_id = move.id
    show_create_draft_btn = fields.Boolean(
        compute="_compute_button_visibility",
        string="Show Create Draft Button"
    )
    show_post_draft_btn = fields.Boolean(
        compute="_compute_button_visibility",
        string="Show Post Draft Button"
    )

    @api.depends("draft_journal_entry_id", "draft_journal_entry_state", "state", "penalties_awards_id.penalty_employee")
    def _compute_button_visibility(self):
        for rec in self:
            # 🚫 Hide buttons if record is draft or cancel
            if rec.state in ("draft", "cancel"):
                rec.show_create_draft_btn = False
                rec.show_post_draft_btn = False

            # ✅ Show create draft button only if penalty_employee = True
            elif not rec.draft_journal_entry_id and rec.penalties_awards_id and rec.penalties_awards_id.penalty_employee:
                rec.show_create_draft_btn = True
                rec.show_post_draft_btn = False

            # Show post button if draft entry exists
            elif rec.draft_journal_entry_state == "draft":
                rec.show_create_draft_btn = False
                rec.show_post_draft_btn = True

            # Otherwise hide both
            else:
                rec.show_create_draft_btn = False
                rec.show_post_draft_btn = False

    def action_post_draft_journal_entry(self):
        for rec in self:
            if not rec.draft_journal_entry_id:
                raise UserError(_("No draft journal entry to post."))
            if rec.draft_journal_entry_id.state != "draft":
                raise UserError(_("Journal Entry is already posted."))
            rec.draft_journal_entry_id.action_post()

    def write(self, vals):
        res = super(GsPenaltiesAwards, self).write(vals)
        for rec in self:
            if 'state' in vals and vals['state'] in ("draft", "cancel"):
                if rec.draft_journal_entry_id:
                    move = rec.draft_journal_entry_id
                    # If posted, reset to draft first
                    if move.state == "posted":
                        move.button_draft()
                    move.unlink()
                    rec.draft_journal_entry_id = False
        return res



class PenaltiesAwardsInstallment(models.Model):
    _name = 'gs.penalties.awards.installment'
    _description = 'Lines of an Installment'
    _order = 'date,name'

    name = fields.Char('Name', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    penalties_awards_id = fields.Many2one('gs.penalties.awards', required=True, ondelete='cascade', readonly=True)
    date = fields.Date('Date')
    is_paid = fields.Boolean('Paid', readonly=True)
    amount = fields.Float('Loan Amount', readonly=True)
    interest = fields.Float('Total Interest', readonly=True)
    ins_interest = fields.Float('Interest', readonly=True)
    installment_amt = fields.Float('Installment Amt', readonly=True)
    total_installment = fields.Float('Total', compute='get_total_installment', readonly=True)
    payslip_id = fields.Many2one('hr.payslip', string='Payslip', readonly=True)
    is_skip = fields.Boolean('Skip Installment', readonly=True)
    payroll_paid = fields.Boolean(default=True)

    @api.depends('installment_amt', 'ins_interest')
    def get_total_installment(self):
        for line in self:
            line.total_installment = line.ins_interest + line.installment_amt

    def action_view_payslip(self):
        if self.payslip_id:
            return {
                'view_mode': 'form',
                'res_id': self.payslip_id.id,
                'res_model': 'hr.payslip',
                'view_type': 'form',
                'type': 'ir.actions.act_window',

            }
