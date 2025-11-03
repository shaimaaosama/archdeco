# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GsShipmentDocuments(models.Model):
    _name = 'gs.shipment.documents'
    _description = 'Shipment Documents'

    name = fields.Char()
    link = fields.Char()
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.company.currency_id.id)
    amount = fields.Integer(string='Amount',)
    date = fields.Date(string='Date',)
    is_required = fields.Boolean(string='Is Required?',)
    product_id = fields.Many2one('product.product', string="Product",)
