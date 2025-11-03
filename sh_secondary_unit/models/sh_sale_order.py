# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError


class ShUomUomInherit(models.Model):
    _inherit = "uom.uom"

    def _compute_quantity(self, qty, to_unit, round=False, rounding_method='UP', raise_if_failure=True):
        """ Convert the given quantity from the current UoM `self` into a given one
            :param qty: the quantity to convert
            :param to_unit: the destination UoM record (uom.uom)
            :param raise_if_failure: only if the conversion is not possible
                - if true, raise an exception if the conversion is not possible (different UoM category),
                - otherwise, return the initial quantity
        """
        if not self or not qty:
            return qty
        self.ensure_one()

        if self != to_unit and self.category_id.id != to_unit.category_id.id:
            if raise_if_failure:
                raise UserError(_('The unit of measure %s defined on the order line doesn\'t belong to the same category as the unit of measure %s defined on the product. Please correct the unit of measure defined on the order line or on the product, they should belong to the same category.') % (self.name, to_unit.name))
            else:
                return qty

        if self == to_unit:
            amount = qty
        else:
            amount = qty / self.factor
            if to_unit:
                amount = amount * to_unit.factor

        if to_unit and round:
            amount = tools.float_round(amount, precision_rounding=to_unit.rounding, rounding_method=rounding_method)

        return amount


class ShSaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    sh_sec_qty = fields.Float(
        "Secondary Qty",
        digits='Product Unit of Measure'
    )
    sh_sec_uom = fields.Many2one("uom.uom", 'Secondary UOM')
    sh_is_secondary_unit = fields.Boolean(
        "Related Sec Unit",
        related="product_id.sh_is_secondary_unit"
    )
    category_id = fields.Many2one(
        "uom.category",
        "Sale UOM Category",
        related="product_uom.category_id"
    )

    @api.onchange('product_uom_qty', 'product_uom')
    def onchange_product_uom_qty_sh(self):
        if self and self.sh_is_secondary_unit and self.sh_sec_uom:
            self.sh_sec_qty = self.product_uom._compute_quantity(
                self.product_uom_qty, self.sh_sec_uom
            )

        float_num = self.sh_sec_qty - int(self.sh_sec_qty)
        int_num = int(self.sh_sec_qty)
        if float_num > 0.25:
            int_num += 1
            self.sh_sec_qty = int_num
        else:
            self.sh_sec_qty = int(self.sh_sec_qty)

    @api.onchange('sh_sec_qty', 'sh_sec_uom')
    def onchange_sh_sec_qty_sh(self):
        if self and self.sh_is_secondary_unit and self.product_uom:
            self.product_uom_qty = self.sh_sec_uom._compute_quantity(
                self.sh_sec_qty, self.product_uom
            )

    @api.onchange('product_id')
    def onchange_secondary_uom(self):
        if self:
            for rec in self:
                if rec.product_id and rec.product_id.sh_is_secondary_unit and rec.product_id.uom_id:
                    rec.sh_sec_uom = rec.product_id.sh_secondary_uom.id
                elif not rec.product_id.sh_is_secondary_unit:
                    rec.sh_sec_uom = False
                    rec.sh_sec_qty = 0.0

    def _prepare_invoice_line(self, **optional_values):
        res = super(ShSaleOrderLine, self)._prepare_invoice_line(
            **optional_values
        )
        res.update({
            'sh_sec_qty': self.sh_sec_qty,
            'sh_sec_uom': self.sh_sec_uom.id,
            })
        return res
