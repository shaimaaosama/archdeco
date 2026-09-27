from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def create(self, vals):
        res = super(SaleOrderLineInherit, self).create(vals)
        if res.product_uom_qty == 0.00:
            res.price_unit = 0.00
            if res.order_id.analytic_account_id:
                res.analytic_distribution = {str(res.order_id.analytic_account_id.id): 100.0}
            res.sh_sec_uom = res.product_id.sh_secondary_uom.id
        return res

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.product_uom_qty == 0.0 and rec.price_unit != 0.00:
                super(SaleOrderLineInherit, rec).write({"price_unit": 0.0}, {'analytic_distribution': {str(rec.order_id.analytic_account_id.id): 100.0}})
        return res

    @api.constrains('price_unit', 'product_template_id', 'product_uom_qty')
    def _check_lowest_price(self):
        for line in self:
            if not line.product_template_id:
                continue

            product = line.product_template_id
            lowest_price = product.lowest_price

            if (not self.env.user.has_group('gs_product_custom.group_allow_product_lowest_price')) and  lowest_price and (line.price_unit < lowest_price and line.product_uom_qty != 0.00):
                raise ValidationError(_( "Product '%(product)s' cannot be sold below the Lowest Allowed Price (%(price)s)." ) % { 'product': product.display_name, 'price': lowest_price, })