from odoo import fields, models, api, _

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    ref2 = fields.Char("Reference 2")