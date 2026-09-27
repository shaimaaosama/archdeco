from odoo import fields, models, api

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        res = super(ProductTemplateInherit, self).create(vals)
        if res.is_storable:
            res.invoice_policy = 'delivery'
        return res

    @api.onchange("is_storable")
    def set_invoice_policy(self):
        if self.is_storable:
            self.invoice_policy = 'delivery'