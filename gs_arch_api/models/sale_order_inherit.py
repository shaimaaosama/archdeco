# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResBranchInherit(models.Model):
    _inherit = 'sale.order'

    transaction_id = fields.Char('Transaction ID')
    ecommerce_note = fields.Char('Ecommerce Note')
