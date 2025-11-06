# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class CustomerLimitWizardInherit(models.TransientModel):
    _inherit = 'customer.limit.wizard'

    is_confirm_wiz_limit = fields.Boolean(compute="_get_default_confirm_wiz_limit")

    def _get_default_confirm_wiz_limit(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.sales.permission'].search([], limit=1)
            rec.is_confirm_wiz_limit = False
            if permission:
                if user in permission.confirm_limit_id.ids:
                    rec.is_confirm_wiz_limit = True


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    is_create_invoice = fields.Boolean(compute="_get_default_create_invoice")
    is_send_by_email = fields.Boolean(compute="_get_default_send_by_email")
    is_confirm = fields.Boolean(compute="_get_default_confirm")
    is_cancel = fields.Boolean(compute="_get_default_cancel")
    is_draft = fields.Boolean(compute="_get_default_draft")
    is_send_pro = fields.Boolean(compute="_get_default_send_pro")
    is_lock = fields.Boolean(compute="_get_default_lock")
    is_unlock = fields.Boolean(compute="_get_default_unlock")
    create_delivery = fields.Boolean(compute="_get_default_create_delivery")
    is_create_del = fields.Boolean(copy=False)
    is_revise = fields.Boolean(compute="_get_default_revise")
    is_set_so = fields.Boolean(compute="_get_default_set_so")
    is_confirm_limit = fields.Boolean(compute="_get_default_confirm_limit")
    is_confirm_sale = fields.Boolean(compute="_get_default_confirm_sale")

    def _action_cancel(self):
        for rec in self:
            rec.is_create_del = False
        return super()._action_cancel()

    def _get_default_create_invoice(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.sales.permission'].search([], limit=1)
            rec.is_create_invoice = False
            if permission:
                if user in permission.create_invoice_id.ids:
                    rec.is_create_invoice = True

    def _get_default_send_by_email(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.sales.permission'].search([], limit=1)
            rec.is_send_by_email = False
            if permission:
                if user in permission.send_by_email_id.ids:
                    rec.is_send_by_email = True

    def _get_default_confirm(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.sales.permission'].search([], limit=1)
            rec.is_confirm = False
            if permission:
                if user in permission.confirm_id.ids:
                    rec.is_confirm = True

    def _get_default_cancel(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.sales.permission'].search([], limit=1)
            rec.is_cancel = False
            if permission:
                if user in permission.cancel_id.ids:
                    rec.is_cancel = True

    def _get_default_draft(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.sales.permission'].search([], limit=1)
            rec.is_draft = False
            if permission:
                if user in permission.draft_id.ids:
                    rec.is_draft = True

    def _get_default_send_pro(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.sales.permission'].search([], limit=1)
            rec.is_send_pro = False
            if permission:
                if user in permission.send_pro_id.ids:
                    rec.is_send_pro = True

    def _get_default_lock(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.sales.permission'].search([], limit=1)
            rec.is_lock = False
            if permission:
                if user in permission.lock_id.ids:
                    rec.is_lock = True

    def _get_default_unlock(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.sales.permission'].search([], limit=1)
            rec.is_unlock = False
            if permission:
                if user in permission.unlock_id.ids:
                    rec.is_unlock = True

    def _get_default_create_delivery(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.sales.permission'].search([], limit=1)
            rec.create_delivery = False
            if permission:
                if user in permission.create_delivery_id.ids and rec.state == 'sale':
                    rec.create_delivery = True

    def _get_default_revise(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.sales.permission'].search([], limit=1)
            rec.is_revise = False
            if permission:
                if user in permission.revise_id.ids and rec.state not in ['revised', 'done', 'sale']:
                    rec.is_revise = True

    def _get_default_set_so(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.sales.permission'].search([], limit=1)
            rec.is_set_so = False
            if permission:
                if user in permission.set_so_id.ids and rec.state == 'revised':
                    rec.is_set_so = True

    def _get_default_confirm_limit(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.sales.permission'].search([], limit=1)
            rec.is_confirm_limit = False
            if permission:
                if user in permission.confirm_limit_id.ids:
                    rec.is_confirm_limit = True

    def _get_default_confirm_sale(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.sales.permission'].search([], limit=1)
            rec.is_confirm_sale = False
            if permission:
                if user in permission.confirm_sale_id.ids:
                    rec.is_confirm_sale = True