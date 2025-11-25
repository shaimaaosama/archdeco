# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResBranchInherit(models.Model):
    _inherit = 'res.branch'

    latitude = fields.Float('Latitude', digits=(10, 7))
    longitude = fields.Float('Longitude', digits=(10, 7))


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    available_soon = fields.Boolean(string='Available Soon ')


class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    available_soon = fields.Boolean(string='Available Soon ')
