# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GsClearanceDocuments(models.Model):
    _name = 'gs.clearance.documents'
    _description = 'Clearance Documents'

    name = fields.Char()
    link = fields.Char()
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.company.currency_id.id)
    amount = fields.Integer(string='Amount',)
    date = fields.Date(string='Date',)
    is_required = fields.Boolean(string='Is Required?',)
    product_id = fields.Many2one('product.product', string="Product",)