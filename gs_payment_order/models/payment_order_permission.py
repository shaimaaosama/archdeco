# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GsPaymentPermissionTracking(models.Model):
    _name = 'gs.payment.order.permission'

    permission_type = fields.Selection([
                                        ('payment_order', 'Payment Order'),
                                         ], required=1, string="Permission Type")
    submit_t_id = fields.Many2many("res.users", "user_id_pay13", "user_id_pay113", "user_id_pay1113", string="Submit")
    approve_t_id = fields.Many2many("res.users", "user_id_pay14", "user_id_pay114", "user_id_pay1114", string="Approve")
    draft_t_id = fields.Many2many("res.users", "user_id_pay11", "user_id_pay111", "user_id_pay1111", string="Set to Draft")
    cancel_t_id = fields.Many2many("res.users", "user_id_pay12", "user_id_pay112", "user_id_pay1112", string="Cancel")
    special_approval_t_id = fields.Many2many("res.users", "user_id_pay15", "user_id_pay115", "user_id_pay1115", string="Special ِApproval")
    create_payment_t_id = fields.Many2many("res.users", "user_id_pay16", "user_id_pay116", "user_id_pay1116", string="Create Payment")
    reject_t_id = fields.Many2many("res.users", "user_id_pay17", "user_id_pay117", "user_id_pay1117", string="Reject")
    checked_t_id = fields.Many2many("res.users", "user_id_pay18", "user_id_pay118", "user_id_pay1118", string="Checked")
    finalize_payment_t_id = fields.Many2many("res.users", "user_id_pay19", "user_id_pay119", "user_id_pay1119", string="Finalize Payment")
    final_check_t_id = fields.Many2many("res.users", "user_id_pay20", "user_id_pay120", "user_id_pay1120", string="Final Check")
    closed_t_id = fields.Many2many("res.users", "user_id_pay20", "user_id_pay120", "user_id_pay1120", string="Closed")
    return_t_id = fields.Many2many("res.users", "user_id_pay21", "user_id_pay121", "user_id_pay1121", string="Return")