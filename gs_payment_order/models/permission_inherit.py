# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GSPurchaseTrackingPermission(models.Model):
    _inherit = 'gs.purchase.tracking.permission'

    create_payment_order_ids = fields.Many2many("res.users", "user_id_pay22", "user_id_pay122", "user_id_pay1122", string="Create Payment Order")


class GSSalesPermission(models.Model):
    _inherit = 'gs.sales.permission'

    create_payment_order_ids = fields.Many2many("res.users", "user_id_pay022", "user_id_pay022", "user_id_pay0122", string="Create Payment Order")


class GSPurchasePermission(models.Model):
    _inherit = 'gs.purchase.permission'

    create_payment_order_ids = fields.Many2many("res.users", "user_id_pay322", "user_id_pay322", "user_id_pay3122", string="Create Payment Order")
