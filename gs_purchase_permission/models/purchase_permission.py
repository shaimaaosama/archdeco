# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GsPurchasePermission(models.Model):
    _name = 'gs.purchase.permission'
    _description = 'Purchase Permission'
    # _rec_name = 'permission_type'

    permission_type = fields.Selection([
                                        ('p_purchase_orders', 'Purchase Orders & Requests for Quotation'),
                                         ], required=1, string="Permission Type")

    create_bill_id = fields.Many2many("res.users", "user_id11", "user_id111", "user_id1111", string="Create Bill")
    send_by_email_id = fields.Many2many("res.users", "user_id12", "user_id112", "user_id1112", string="Send by Email")
    print_quotation_id = fields.Many2many("res.users", "user_id13", "user_id113", "user_id1113", string="Print RFQ")
    confirm_id = fields.Many2many("res.users", "user_id14", "user_id114", "user_id1114", string="Confirm")
    approve_id = fields.Many2many("res.users", "user_id15", "user_id115", "user_id1115", string="Approve Order")
    confirm_rem_mail_id = fields.Many2many("res.users", "user_id16", "user_id116", "user_id1116", string="Confirm Receipt Date")
    draft_id = fields.Many2many("res.users", "user_id17", "user_id117", "user_id1117", string="Set to Draft")
    cancel_id = fields.Many2many("res.users", "user_id18", "user_id118", "user_id1118", string="Cancel")
    lock_id = fields.Many2many("res.users", "user_id19", "user_id119", "user_id1119", string="Lock")
    unlock_id = fields.Many2many("res.users", "user_id110", "user_id1110", "user_id11110", string="Unlock")
    view_picking_id = fields.Many2many("res.users", "user_id111", "user_id1111", "user_id11111", string="Receive Products")
    create_tracking_id = fields.Many2many("res.users", "user_id113", "user_id1113", "user_id11113", string="Create Tracking")