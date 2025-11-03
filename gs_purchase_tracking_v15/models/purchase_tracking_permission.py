# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GsPurchasePermissionTracking(models.Model):
    _name = 'gs.purchase.tracking.permission'
    _description = 'Purchase Tracking Permission'
    # _rec_name = 'permission_type'

    permission_type = fields.Selection([
                                        ('p_purchase_tracking', 'Exterior Purchase Order'),
                                        ('p_shipment_tracking', 'Shipment Tracking'),
                                         ], required=1, string="Permission Type")

    draft_t_id = fields.Many2many("res.users", "user_id_tp11", "user_id_tp111", "user_id_tp1111", string="Set to Draft")
    cancel_t_id = fields.Many2many("res.users", "user_id_tp12", "user_id_tp112", "user_id_tp1112", string="Cancel")
    submit_t_id = fields.Many2many("res.users", "user_id_tp13", "user_id_tp113", "user_id_tp1113", string="Submit")
    approve_t_id = fields.Many2many("res.users", "user_id_tp14", "user_id_tp114", "user_id_tp1114", string="Approve")
    create_receipt_t_id = fields.Many2many("res.users", "user_id_tp15", "user_id_tp115", "user_id_tp1115", string="Create Receipt")
    create_bill_t_id = fields.Many2many("res.users", "user_id_tp16", "user_id_tp116", "user_id_tp1116", string="Create Bill")
    lock_t_id = fields.Many2many("res.users", "user_id_tp17", "user_id_tp118", "user_id_tp1119", string="Lock")
    unlock_t_id = fields.Many2many("res.users", "user_id_tp18", "user_id_tp118", "user_id_tp1119", string="Unlock")

    draft_st_id = fields.Many2many("res.users", "user_id_st11", "user_id_st111", "user_id_st1111", string="Set to Draft")
    cancel_st_id = fields.Many2many("res.users", "user_id_st12", "user_id_st112", "user_id_st1112", string="Cancel")
    submit_st_id = fields.Many2many("res.users", "user_id_st13", "user_id_st113", "user_id_st1113", string="Submit")
    confirmed_st_id = fields.Many2many("res.users", "user_id_st14", "user_id_st114", "user_id_st1114", string="Confirmed")
    booking_st_id = fields.Many2many("res.users", "user_id_st15", "user_id_st115", "user_id_st1115", string="Booking")
    booked_st_id = fields.Many2many("res.users", "user_id_st16", "user_id_st116", "user_id_st1116", string="Booked")
    loading_st_id = fields.Many2many("res.users", "user_id_st17", "user_id_st117", "user_id_st1117", string="Loading")
    loaded_st_id = fields.Many2many("res.users", "user_id_st18", "user_id_st118", "user_id_st1118", string="Loaded")
    on_board_st_id = fields.Many2many("res.users", "user_id_st19", "user_id_st119", "user_id_st1119", string="On Board")
    departed_st_id = fields.Many2many("res.users", "user_id_st110", "user_id_st1110", "user_id_st11110", string="Departed")
    doc_collect_st_id = fields.Many2many("res.users", "user_id_st111", "user_id_st1111", "user_id_st11111", string="Doc Collect")
    issue_insurance_st_id = fields.Many2many("res.users", "user_id_st112", "user_id_st1112", "user_id_st11112", string="Issue Insurance")
    arrived_st_id = fields.Many2many("res.users", "user_id_st113", "user_id_st1113", "user_id_st11113", string="Arrived")
    under_clearance_st_id = fields.Many2many("res.users", "user_id_st114", "user_id_st1114", "user_id_st11114", string="Under Clearance")
    cleared_st_id = fields.Many2many("res.users", "user_id_st115", "user_id_st1115", "user_id_st11115", string="Cleared")
    paneling_delivery_st_id = fields.Many2many("res.users", "user_id_st116", "user_id_st1116", "user_id_st11116", string="Paneling Delivery")
    received_st_id = fields.Many2many("res.users", "user_id_st117", "user_id_st1117", "user_id_st11117", string="Received")
