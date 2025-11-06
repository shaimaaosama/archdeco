# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResUsersInheritPO(models.Model):
    _inherit = 'res.users'

    payment_type_po_ids = fields.Many2many('gs.payment.type', 'payment_type_po_ids01', 'payment_type_po_ids001',
                                        'payment_type_po_ids0001', string='Payment Type',)

