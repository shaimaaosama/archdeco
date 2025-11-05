# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    is_max_view = fields.Boolean(string="Is Max view?")
    max_view = fields.Float(string='Max View',)


class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    is_max_view = fields.Boolean(string="Is Max view?")
    max_view = fields.Float(string='Max View',)


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('sh_sec_qty')
    def _onchange_product_id_gs_sales_max(self):
        for rec in self:
            if rec.sh_sec_qty:
                if rec.product_id:
                    if rec.product_id.is_max_view:
                        if rec.sh_sec_qty > rec.product_id.max_view:
                            raise ValidationError(_("You have exceeded the limit."))
