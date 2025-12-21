# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    lowest_price = fields.Monetary(
        string="Lowest Allowed Price",
        currency_field='currency_id',
    )


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('price_unit', 'product_template_id', 'product_uom_qty')
    def _check_lowest_price(self):
        for line in self:
            if not line.product_template_id:
                continue

            product = line.product_template_id
            lowest_price = product.lowest_price

            if lowest_price and line.price_unit < lowest_price:
                raise ValidationError(_(
                    "Product '%(product)s' cannot be sold below the Lowest Allowed Price (%(price)s)."
                ) % {
                                          'product': product.display_name,
                                          'price': lowest_price,
                                      })