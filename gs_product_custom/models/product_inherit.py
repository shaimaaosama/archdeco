# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    lowest_price = fields.Monetary(
        string="Lowest Allowed Price",
        currency_field='currency_id',
    )

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def_name = fields.Char(
        string="Description" )
    @api.model
    def _get_deferred_lines_values(self, account_id, balance, ref, analytic_distribution, line=None):
        return {
            'account_id': account_id,
            # line either be a dict with ids (coming from SQL query), or a real account.move.line object
            'product_id': line['product_id'] if isinstance(line, dict) else line['product_id'].id,
            'product_category_id': line['product_category_id'] if isinstance(line, dict) else line['product_category_id'].id,
            'balance': balance,
            'name': ref,
            'def_name': line['name'],
            'analytic_distribution': analytic_distribution,
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('price_unit', 'product_template_id', 'product_uom_qty')
    def _check_lowest_price(self):
        for line in self:
            if not line.product_template_id:
                continue

            product = line.product_template_id
            lowest_price = product.lowest_price

            if (not self.env.user.has_group('gs_product_custom.group_allow_product_lowest_price')) and  lowest_price and line.price_unit < lowest_price:
                raise ValidationError(_(
                    "Product '%(product)s' cannot be sold below the Lowest Allowed Price (%(price)s)."
                ) % {
                                          'product': product.display_name,
                                          'price': lowest_price,
                                      })