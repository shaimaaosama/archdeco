# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    is_create_bill = fields.Boolean(compute="_get_default_create_bill")
    is_send_by_email = fields.Boolean(compute="_get_default_send_by_email")
    is_print_quotation = fields.Boolean(compute="_get_default_print_quotation")
    is_confirm = fields.Boolean(compute="_get_default_confirm")
    is_cancel = fields.Boolean(compute="_get_default_cancel")
    is_draft = fields.Boolean(compute="_get_default_draft")
    is_approve = fields.Boolean(compute="_get_default_approve")
    is_lock = fields.Boolean(compute="_get_default_lock")
    is_unlock = fields.Boolean(compute="_get_default_unlock")
    is_confirm_rem_mail = fields.Boolean(compute="_get_default_confirm_rem_mail")
    is_view_picking = fields.Boolean(compute="_get_default_view_picking")
    is_create_receipt = fields.Boolean()
    is_create_tracking = fields.Boolean(compute="_get_default_create_tracking")

    def _get_default_create_bill(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.permission'].search([], limit=1)
            rec.is_create_bill = False
            if permission:
                if user in permission.create_bill_id.ids:
                    rec.is_create_bill = True

    def _get_default_send_by_email(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.permission'].search([], limit=1)
            rec.is_send_by_email = False
            if permission:
                if user in permission.send_by_email_id.ids:
                    rec.is_send_by_email = True

    def _get_default_print_quotation(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.permission'].search([], limit=1)
            rec.is_print_quotation = False
            if permission:
                if user in permission.print_quotation_id.ids:
                    rec.is_print_quotation = True

    def _get_default_confirm(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.permission'].search([], limit=1)
            rec.is_confirm = False
            if permission:
                if user in permission.confirm_id.ids:
                    rec.is_confirm = True

    def _get_default_cancel(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.permission'].search([], limit=1)
            rec.is_cancel = False
            if permission:
                if user in permission.cancel_id.ids:
                    rec.is_cancel = True

    def _get_default_draft(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.permission'].search([], limit=1)
            rec.is_draft = False
            if permission:
                if user in permission.draft_id.ids:
                    rec.is_draft = True

    def _get_default_approve(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.permission'].search([], limit=1)
            rec.is_approve = False
            if permission:
                if user in permission.approve_id.ids:
                    rec.is_approve = True

    def _get_default_lock(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.permission'].search([], limit=1)
            rec.is_lock = False
            if permission:
                if user in permission.lock_id.ids:
                    rec.is_lock = True

    def _get_default_unlock(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.permission'].search([], limit=1)
            rec.is_unlock = False
            if permission:
                if user in permission.unlock_id.ids:
                    rec.is_unlock = True

    def _get_default_confirm_rem_mail(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.permission'].search([], limit=1)
            rec.is_confirm_rem_mail = False
            if permission:
                if user in permission.confirm_rem_mail_id.ids:
                    rec.is_confirm_rem_mail = True

    def _get_default_view_picking(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.permission'].search([], limit=1)
            rec.is_view_picking = False
            if permission:
                if user in permission.view_picking_id.ids:
                    rec.is_view_picking = True

    def _get_default_create_tracking(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.permission'].search([], limit=1)
            rec.is_create_tracking = False
            if permission:
                if user in permission.create_tracking_id.ids and rec.state == 'purchase':
                    rec.is_create_tracking = True
