# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GsSalesPermission(models.Model):
    _name = 'gs.sales.permission'
    _description = 'Sales Permission'
    _rec_name = 'permission_type'

    permission_type = fields.Selection([('s_quotations', 'Quotations'),
                                         ], required=1, string="Permission Type")

    create_invoice_id = fields.Many2many("res.users", "user_id01", "user_id001", "user_id0001", string="Create Invoice")
    send_by_email_id = fields.Many2many("res.users", "user_id02", "user_id002", "user_id0002", string="Send by Email")
    confirm_id = fields.Many2many("res.users", "user_id03", "user_id003", "user_id0003", string="Confirm")
    cancel_id = fields.Many2many("res.users", "user_id04", "user_id004", "user_id0004", string="Cancel")
    draft_id = fields.Many2many("res.users", "user_id05", "user_id005", "user_id0005", string="Set to Quotation")
    send_pro_id = fields.Many2many("res.users", "user_id06", "user_id006", "user_id0006", string="Send PRO-FORMA Invoice")
    lock_id = fields.Many2many("res.users", "user_id07", "user_id007", "user_id0007", string="Lock")
    unlock_id = fields.Many2many("res.users", "user_id08", "user_id008", "user_id0008", string="Unlock")
    create_delivery_id = fields.Many2many("res.users", "user_id09", "user_id009", "user_id0009", string="Create Delivery")
    revise_id = fields.Many2many("res.users", "user_id010", "user_id0010", "user_id00010", string="Make Revise Sale Quotation")
    set_so_id = fields.Many2many("res.users", "user_id011", "user_id0011", "user_id00011", string="Set SO")
    confirm_limit_id = fields.Many2many("res.users", "user_id012", "user_id0012", "user_id00012", string="Confirm (limit)")
    confirm_sale_id = fields.Many2many("res.users", "user_id013", "user_id0013", "user_id00013", string="Confirm Sale")