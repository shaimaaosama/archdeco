# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class GsPaymentOrder(models.Model):
    _name = 'gs.payment.order'
    _description = 'Payment Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_user(self):
        return self.env.user

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('gs.payment.order.sequence') or _('New')
        result = super(GsPaymentOrder, self).create(vals)
        result._payment_is_created()
        return result

    def _payment_is_created(self):
        for rec in self:
            rec.helpdesk_ticket_id.is_create_payment_new = True
            rec.sale_order_id.is_create_payment_new = True
            rec.purchase_order_id.is_create_payment_new = True
            rec.purchase_tracking_id.is_create_payment_new = True

    name = fields.Char('Reference', required=True, copy=False, readonly=True,
                       index=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Partner')
    create_date = fields.Datetime(string='Create Date',  default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Create By', default=_get_default_user)
    payment_due_date = fields.Date(string='Payment Due Date',  default=lambda self: fields.Date.context_today(self))
    payment_type_id = fields.Many2one('gs.payment.type', string='Payment Type ')
    journal_id = fields.Many2one('account.journal', string='Payment Journal', domain=[('type', 'in', ['bank', 'cash'])])
    amount = fields.Float(string='Amount',)
    amount_payment = fields.Float(string='Amount Payment',)
    amount_payment_available = fields.Float(string='Amount Payment Available',)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id.id)
    exchange_rate = fields.Float(string='Exchange rate')
    description = fields.Text(string="Description", )
    attached_file = fields.Binary(string='Attached File')
    state = fields.Selection(string='State', selection=[
                                                    ('draft', 'Draft'),
                                                    ('submit', 'Submitted'),
                                                    ('checked', 'Checked'),
                                                    ('approve', 'Approved'),
                                                    ('special_approval', 'Special Approval'),
                                                    ('special_approved', 'Special Approved'),
                                                    ('issue_payment', 'Issue Payment'),
                                                    ('finalize_payment', 'Finalize Payment'),
                                                    ('final_check', 'Final Check'),
                                                    ('close', 'Closed'),
                                                    ('cancel', 'Cancel'),
                                                    ('refused', 'Refused'),
                                                    ], default='draft', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('res.branch', string="Branch", default=lambda self: self.env.user.branch_id)
    payment_id = fields.Many2one('account.payment')
    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket')
    inv_create_payment = fields.Boolean(compute='_compute_inv_create_payment')
    hide_special_approval = fields.Boolean()
    journal_items_ids = fields.Many2many('account.move.line', 'journal_items_ids00', 'journal_items_ids01', 'journal_items_ids02', string='Journal Items', copy=False)
    payment_order_history_ids = fields.One2many('gs.payment.order.history', 'payment_order_id')
    sale_order_id = fields.Many2one('sale.order')
    purchase_order_id = fields.Many2one('purchase.order')
    purchase_tracking_id = fields.Many2one('gs.purchase.tracking')
    recipient_users = fields.Text()

    def send_template_email(self, users):

        recipient_users = []
        for recipient in users:
            if recipient.employee_id.work_email not in recipient_users:
                recipient_users.append(recipient.employee_id.work_email)

        recipient_users = '[%s]' % ', '.join(map(str, recipient_users))
        self.recipient_users = recipient_users

        template_id = self.env.ref('gs_payment_order.email_template_for_finalize_payment_payment_order').id
        template = self.env['mail.template'].browse(template_id)
        template.send_mail(self.id, force_send=True)

    def make_activity_user(self, user):
        date_deadline = fields.Date.today()
        note = _("Please Review This Payment Order")
        summary = _("Payment Order")

        self.sudo().activity_schedule(
            'mail.mail_activity_data_todo', date_deadline,
            note=note,
            user_id=user.id,
            res_id=self.id,
            summary=summary
        )

    def _compute_inv_create_payment(self):
        for rec in self:
            payment = self.env['account.payment'].search([('payment_order_id', '=', rec.id)])
            amount = 0
            rec.inv_create_payment = False
            if payment:
                for pay in payment:
                    amount += pay.amount
                if amount == rec.amount and rec.state in ['approve', 'issue_payment']:
                    rec.inv_create_payment = True
            else:
                rec.amount_payment = 0
                rec.amount_payment_available = rec.amount

    def action_create_payment(self, amount, journal_id, currency_id):
        vals = {
            'payment_order_id': self.id,
            'partner_id': self.partner_id.id,
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'amount': amount,
            'currency_id': currency_id.id,
            'journal_id': journal_id.id,
            'company_id': self.company_id.id,
            'branch_id': self.branch_id.id,
            'date': self.payment_due_date,
            'memo': self.description,
        }
        payment = self.env['account.payment'].create(vals)
        self.amount_payment += amount
        self.amount_payment_available -= amount
        if self.amount_payment_available > self.amount_payment:
            self.hide_special_approval = True
        if self.amount_payment_available == 0:
            self.state = 'issue_payment'
        # if self.inv_create_payment:
        #     self.state = 'close'

    def action_submit(self):
        self.write({'state': 'submit'})

    def action_approve(self):
        self.write({'state': 'approve'})

    def action_refused(self):
        self.write({'state': 'refused'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.hide_special_approval = False
        self.write({'state': 'draft'})

    def action_checked(self):
        self.write({'state': 'checked'})

    def action_finalize_payment(self):
        for rec in self:
            payment_type = self.env['gs.payment.type'].search([('id', '=', rec.payment_type_id.id)], limit=1)
            if payment_type:
                for user in payment_type.finalize_payment_user_ids:
                    rec.make_activity_user(user)
                    rec.send_template_email(user)
        self.write({'state': 'finalize_payment'})

    def action_final_check(self):
        self.write({'state': 'final_check'})

    def action_special_approved(self):
        self.write({'state': 'special_approved'})

    def action_close(self):
        payment = self.env['account.payment'].search([('payment_order_id', '=', self.id)])
        amount = 0
        is_posted = False
        for pay in payment:
            if pay.state == 'posted':
                amount += pay.amount
                is_posted = True
        if is_posted and amount == self.amount:
            self.write({'state': 'close'})
        else:
            amount = 0
            for pay in payment:
                amount += pay.amount
            raise ValidationError(
                _('Attention !! your Payment is not posted or amount in payment order not equal amount in payment'
                  ' , amount in payment is (%s)' % (amount)))

    def action_crate_special_approval(self, user_ids):
        template_id = self.env.ref("gs_payment_order.email_template_for_special_approval_payment_order")
        groups = self.env['res.groups'].search([('id', '=', self.env.ref('gs_payment_order.group_special_approval').id)]).users
        for user in user_ids:
            if template_id and user:
                template_id.sudo().send_mail(self.id, force_send=True, email_values={
                    'email_from': self.env.user.email, 'email_to': user.email})
                self.write({'state': 'special_approval'})

    @api.onchange('currency_id')
    def _onchange_currency_id(self):
        for rec in self:
            rec.exchange_rate = rec.currency_id.rate

    @api.onchange('amount')
    def _onchange_amount(self):
        for rec in self:
            if rec.amount:
                rec.amount_payment_available = rec.amount

    payment_count = fields.Integer("Shipment count", compute='_compute_payment_count')

    def action_view_payment(self):
        return {
            'name': _('Payment'),
            'domain': [('payment_order_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'account.payment',
            'view_id': False,
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
        }

    def _compute_payment_count(self):
        payment = self.env['account.payment'].search_count([('payment_order_id', '=', self.id)])
        self.payment_count = payment

    is_cancel = fields.Boolean(compute="_get_default_cancel")
    is_draft = fields.Boolean(compute="_get_default_draft")
    is_approve = fields.Boolean(compute="_get_default_approve")
    is_submit = fields.Boolean(compute="_get_default_submit")
    is_special_approval = fields.Boolean(compute="_get_default_special_approval")
    is_create_payment = fields.Boolean(compute="_get_default_create_payment")
    is_reject = fields.Boolean(compute="_get_default_reject")
    is_checked = fields.Boolean(compute="_get_default_checked")
    is_finalize_payment = fields.Boolean(compute="_get_default_finalize_payment")
    is_final_check = fields.Boolean(compute="_get_default_final_check")
    is_closed = fields.Boolean(compute="_get_default_closed")
    is_return = fields.Boolean(compute="_get_default_return")

    def _get_default_submit(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.payment.order.permission'].search(
                [('permission_type', '=', 'payment_order')], limit=1)
            rec.is_submit = False
            if permission:
                if user in permission.submit_t_id.ids:
                    rec.is_submit = True

    def _get_default_special_approval(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.payment.order.permission'].search(
                [('permission_type', '=', 'payment_order')], limit=1)
            rec.is_special_approval = False
            if permission:
                if user in permission.special_approval_t_id.ids:
                    rec.is_special_approval = True

    def _get_default_create_payment(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.payment.order.permission'].search(
                [('permission_type', '=', 'payment_order')], limit=1)
            rec.is_create_payment = False
            if permission:
                if user in permission.create_payment_t_id.ids:
                    rec.is_create_payment = True

    def _get_default_reject(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.payment.order.permission'].search(
                [('permission_type', '=', 'payment_order')], limit=1)
            rec.is_reject = False
            if permission:
                if user in permission.reject_t_id.ids:
                    rec.is_reject = True

    def _get_default_approve(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.payment.order.permission'].search(
                [('permission_type', '=', 'payment_order')], limit=1)
            rec.is_approve = False
            if permission:
                if user in permission.approve_t_id.ids:
                    rec.is_approve = True

    def _get_default_cancel(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.payment.order.permission'].search(
                [('permission_type', '=', 'payment_order')], limit=1)
            rec.is_cancel = False
            if permission:
                if user in permission.cancel_t_id.ids:
                    rec.is_cancel = True

    def _get_default_draft(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.payment.order.permission'].search(
                [('permission_type', '=', 'payment_order')], limit=1)
            rec.is_draft = False
            if permission:
                if user in permission.draft_t_id.ids:
                    rec.is_draft = True

    def _get_default_checked(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.payment.order.permission'].search(
                [('permission_type', '=', 'payment_order')], limit=1)
            rec.is_checked = False
            if permission:
                if user in permission.checked_t_id.ids:
                    rec.is_checked = True

    def _get_default_finalize_payment(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.payment.order.permission'].search(
                [('permission_type', '=', 'payment_order')], limit=1)
            rec.is_finalize_payment = False
            if permission:
                if user in permission.finalize_payment_t_id.ids:
                    rec.is_finalize_payment = True

    def _get_default_final_check(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.payment.order.permission'].search(
                [('permission_type', '=', 'payment_order')], limit=1)
            rec.is_final_check = False
            if permission:
                if user in permission.final_check_t_id.ids:
                    rec.is_final_check = True

    def _get_default_closed(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.payment.order.permission'].search(
                [('permission_type', '=', 'payment_order')], limit=1)
            rec.is_closed = False
            if permission:
                if user in permission.closed_t_id.ids:
                    rec.is_closed = True

    def _get_default_return(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.payment.order.permission'].search(
                [('permission_type', '=', 'payment_order')], limit=1)
            rec.is_return = False
            if permission:
                if user in permission.return_t_id.ids:
                    rec.is_return = True


class PaymentOrderHistory(models.Model):
    _name = 'gs.payment.order.history'

    payment_order_id = fields.Many2one('gs.payment.order')
    date = fields.Datetime(string='Date')
    note = fields.Char(string='Note')
    user_id = fields.Many2one('res.users', string='Return By')