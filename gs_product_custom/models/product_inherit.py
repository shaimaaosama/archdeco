# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    lowest_price = fields.Float(
        'Lowest Price',
        digits='Product Price',
    )


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order.line'

    lowest_price = fields.Float(
        'Lowest Price',
        digits='Product Price', related="product_id.lowest_price"
    )

    @api.onchange('price_unit')
    def _onchange_gs_price_unit(self):
        for rec in self:
            if rec.lowest_price and rec.price_unit:
                if rec.lowest_price > rec.price_unit:
                    raise ValidationError(
                        _("The lowest price is greater than the unit price.")
                    )
