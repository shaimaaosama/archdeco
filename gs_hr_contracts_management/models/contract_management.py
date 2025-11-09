# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
import datetime


class GsSaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_management_id = fields.Many2one('gs.contract.management', string='Contract Management', tracking=True, )


class GsPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    contract_management_id = fields.Many2one('gs.contract.management', string='Contract Management', tracking=True, )


class GsContractManagement(models.Model):
    _name = 'gs.contract.management'
    _description = 'Contract Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('contract_payment_schedule') or _('New')
        res = super(GsContractManagement, self).create(vals)
        return res

    # def write(self, values):
    #     result = super(GsContractManagement, self).write(values)
    #     self._get_contact_payment_ids()
    #     return result

    name = fields.Char(string="Contract Serial Number", track_visibility="onchange", required=True,
                       copy=False, readonly=True,
                       index=True, default=lambda self: _('New'))
    ref = fields.Char(string='Ref.')
    description = fields.Text(tracking=True)
    company_id = fields.Many2one('res.company', string='Company', tracking=True, )
    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True)
    type_of_contract = fields.Many2one('gs.type.of.contracts', string='Contract Classification', tracking=True, )
    start_date = fields.Date(string="Start Date", tracking=True, )
    end_date = fields.Date(string="End Date", tracking=True, )

    amount = fields.Integer(string="Amount", tracking=True)
    number_of_payments = fields.Integer(string="Number Of Payments", compute="get_contact_payment_count", tracking=True)

    days = fields.Integer(string="Days To End Contract", compute="_get_available_days", store=True, tracking=True)
    notice_period = fields.Integer(string="Notice period", tracking=True)
    date_renew = fields.Date("Renew Date", tracking=True, )
    date_remind_id = fields.Many2one('gs.remind', string='Reminders', tracking=True, )
    contact_payment_ids = fields.One2many('gs.contact.payment.schedule', 'contract_barcode_id', string='Payments', tracking=True, )

    status = fields.Selection(string='Status',
                              selection=[('draft', 'Draft'),
                                         ('running', 'Running'),
                                         ('expire', 'Expire'),
                                         ('canceled', 'Canceled'),
                                         ], default='draft',
                              required=False, tracking=True)
    active = fields.Boolean(default=True, tracking=True, store=True)
    contract_type = fields.Selection(string='Contract Type',
                              selection=[('sales', 'Sales'),
                                         ('purchase', 'Purchase'), ],
                              required=False, tracking=True, )

    attachment = fields.Boolean(tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', 'contract_management_attachment_rel', 'contract_management_template_id',
                                      'contract_management_attachment_id', 'Attachments', tracking=True, )

    notes = fields.Html(string='Notes', required=False)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', tracking=True)
    # analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', tracking=True)
    is_renew = fields.Boolean(string='Is Renew?', tracking=True)
    total_payment = fields.Integer(string='Total Payment', compute='_get_total', tracking=True)
    run_com = fields.Boolean(compute="_onchange_active")
    is_get_data_notification = fields.Boolean()

    @api.onchange('date_renew')
    def onchange_method(self):
        if self.is_get_data_notification:
            self.is_get_data_notification = False

    def _onchange_active(self):
        for rec in self:
            rec.run_com = True
            cont_pay = self.env["gs.contact.payment.schedule"].search([("contract_barcode_id", "=", rec.id), ("active", "=", False)])
            for con in cont_pay:
                con.active = rec.active
                con.state = rec.status

            cont_pay2 = self.env["gs.contact.payment.schedule"].search([("contract_barcode_id", "=", rec.id), ("active", "=", True)])
            for con2 in cont_pay2:
                con2.active = rec.active
                con2.state = rec.status

    def _get_total(self):
        for rec in self:
            total = 0
            for line in rec.contact_payment_ids:
                total += line.amount
            rec.total_payment = total

    def get_contact_payment_ids(self):
        contact_payment = self.env['gs.contact.payment.schedule'].search([('contract_barcode_id', '=', self.id)])
        lines = [(5, 0, 0)]
        for payment in contact_payment:
            vals = {
                'contract_barcode_id': payment.id,
                'payment_schedule': payment.payment_schedule,
                'amount': payment.amount,
                'due_date': payment.due_date,
                'status': payment.status,
            }
            lines.append((0, 0, vals))
        self.contact_payment_ids = lines

    def get_contact_payment_count(self):
        for rec in self:
            count = self.env['gs.contact.payment.schedule'].search_count([('contract_barcode_id', '=', rec.id)])
            self.number_of_payments = count

    @api.onchange('notice_period', 'end_date')
    def _onchange_date_end(self):
        for rec in self:
            if rec.days and rec.notice_period:
                rec.date_renew = rec.end_date - relativedelta(days=rec.notice_period)
            elif rec.notice_period == 0:
                rec.date_renew = rec.end_date

    @api.depends('end_date')
    def _get_available_days(self):
        today = fields.Date.context_today(self)
        rd = relativedelta(self.end_date, today)
        year_days = (rd.years * 12) * 31
        months_days = rd.months * 31
        self.days = rd.days + months_days + year_days

    def action_running(self):
        self.write({'status': 'running'})
        return True

    def action_expire(self):
        self.write({'status': 'expire'})
        return True

    def action_cancel(self):
        self.write({'status': 'canceled'})
        return True

    sales_count = fields.Integer(compute='get_gs_sales_count')

    def open_gs_sales(self):
        return {
            'name': _('Sales'),
            'domain': [('contract_management_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'sale.order',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_contract_management_id': self.id,
            }
        }

    def get_gs_sales_count(self):
        count = self.env['sale.order'].search_count([('contract_management_id', '=', self.id)])
        self.sales_count = count

    purchase_count = fields.Integer(compute='get_gs_purchase_count')

    def open_gs_purchase(self):
        return {
            'name': _('purchase'),
            'domain': [('contract_management_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'purchase.order',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_contract_management_id': self.id,
            }
        }

    def get_gs_purchase_count(self):
        count = self.env['purchase.order'].search_count([('contract_management_id', '=', self.id)])
        self.purchase_count = count

    product = fields.Boolean()
    product_id = fields.Many2one('product.product', string='Product Name', tracking=True, )

    asset = fields.Boolean()
    asset_id = fields.Many2one('account.asset', string='Asset Name', tracking=True, )

    def action_create_sales(self):
        for rec in self:
            vals = {
                'contract_management_id': rec.id,
                'partner_id': rec.partner_id.id,
            }
            self.env['sale.order'].create(vals)

    def action_create_purchase(self):
        for rec in self:
            vals = {
                'contract_management_id': rec.id,
                'partner_id': rec.partner_id.id,
            }
            self.env['purchase.order'].create(vals)