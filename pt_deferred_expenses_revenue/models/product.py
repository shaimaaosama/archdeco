# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    property_account_deferred_expense_id = fields.Many2one(
        'account.account', 
        string="Deferred Expense Account",

    )
    property_account_deferred_revenue_id = fields.Many2one(
        'account.account', 
        string="Deferred Revenue Account",

    )

