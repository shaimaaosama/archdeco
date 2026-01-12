# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import json

class GSAccountPayment(models.Model):
    _inherit = 'helpdesk.ticket'

    is_create_payment_new = fields.Boolean()
    payment_count = fields.Integer("Payment count", compute='_compute_payment_count')

    def action_view_payment(self):
        return {
            'name': _('Payment Order'),
            'domain': [('helpdesk_ticket_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'gs.payment.order',
            'view_id': False,
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
        }

    def _compute_payment_count(self):
        payment = self.env['gs.payment.order'].search_count([('helpdesk_ticket_id', '=', self.id)])
        self.payment_count = payment

class GSSaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'analytic.domain.mixin']

    is_create_payment_new = fields.Boolean()
    payment_count = fields.Integer("Payment count", compute='_compute_payment_count')
    analytic_account_id = fields.Many2one('account.analytic.account')

    readonly_analytic = fields.Boolean(compute="_compute_readonly_analytic")
    @api.depends('analytic_account_id')
    def _compute_readonly_analytic(self):
        for record in self:
            allowed = self.env.user.account_analytic_account_ids or []
            if record.analytic_account_id and record.analytic_account_id in allowed:
               record.readonly_analytic = False
            elif not record.analytic_account_id:
                record.readonly_analytic = False

            else:
                record.readonly_analytic = True

    # is_create_payment_order = fields.Boolean(compute="_get_default_create_payment_order")

    # def _get_default_create_payment_order(self):
    #     for rec in self:
    #         user = rec.env.user.id
    #         permission = self.env['gs.sales.permission'].search([], limit=1)
    #         rec.is_create_payment_order = False
    #         if permission:
    #             if user in permission.create_payment_order_ids.ids:
    #                 rec.is_create_payment_order = True

    def action_view_payment(self):
        return {
            'name': _('Payment Order'),
            'domain': [('sale_order_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'gs.payment.order',
            'view_id': False,
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
        }

    def _compute_payment_count(self):
        payment = self.env['gs.payment.order'].search_count([('sale_order_id', '=', self.id)])
        self.payment_count = payment

    @api.constrains('analytic_account_id', 'order_line')
    @api.onchange('analytic_account_id','order_line')
    def _onchange_analytic_account_id(self):
        self.clear_caches()
        if self.analytic_account_id:
            self.order_line.update({'analytic_distribution': {self.analytic_account_id.id:100}})

class GSPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_create_payment_new = fields.Boolean()
    payment_count = fields.Integer("Payment count", compute='_compute_payment_count')
    # is_create_payment_order = fields.Boolean(compute="_get_default_create_payment_order")

    # def _get_default_create_payment_order(self):
    #     for rec in self:
    #         user = rec.env.user.id
    #         permission = self.env['gs.purchase.permission'].search([], limit=1)
    #         rec.is_create_payment_order = False
    #         if permission:
    #             if user in permission.create_payment_order_ids.ids:
    #                 rec.is_create_payment_order = True

    def action_view_payment(self):
        return {
            'name': _('Payment Order'),
            'domain': [('purchase_order_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'gs.payment.order',
            'view_id': False,
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
        }

    def _compute_payment_count(self):
        payment = self.env['gs.payment.order'].search_count([('purchase_order_id', '=', self.id)])
        self.payment_count = payment


class GSPurchaseTracking(models.Model):
    _inherit = 'gs.purchase.tracking'

    is_create_payment_new = fields.Boolean()
    payment_count = fields.Integer("Payment count", compute='_compute_payment_count')
    # is_create_payment_order = fields.Boolean(compute="_get_default_create_payment_order")

    # def _get_default_create_payment_order(self):
    #     for rec in self:
    #         user = rec.env.user.id
    #         permission = self.env['gs.purchase.tracking.permission'].search([('permission_type', '=', 'p_purchase_tracking')], limit=1)
    #         rec.is_create_payment_order = False
    #         if permission:
    #             if user in permission.create_payment_order_ids.ids:
    #                 rec.is_create_payment_order = True

    def action_view_payment(self):
        return {
            'name': _('Payment Order'),
            'domain': [('purchase_tracking_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'gs.payment.order',
            'view_id': False,
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
        }

    def _compute_payment_count(self):
        payment = self.env['gs.payment.order'].search_count([('purchase_tracking_id', '=', self.id)])
        self.payment_count = payment