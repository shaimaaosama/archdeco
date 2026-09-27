from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def create(self, vals):
        res = super(SaleOrderLineInherit, self).create(vals)

        if res.product_uom_qty == 0.00:
            res.price_unit = 0.00

            if res.order_id.analytic_account_id:
                res.analytic_distribution = {
                    str(res.order_id.analytic_account_id.id): 100.0
                }

            res.sh_sec_uom = res.product_id.sh_secondary_uom.id

        return res

    @api.constrains('price_unit', 'product_template_id', 'product_uom_qty')
    def _check_lowest_price(self):
        for line in self:
            if not line.product_template_id:
                continue

            product = line.product_template_id
            lowest_price = product.lowest_price

            if (
                not self.env.user.has_group(
                    'gs_product_custom.group_allow_product_lowest_price'
                )
                and lowest_price
                and line.price_unit < lowest_price
                and line.product_uom_qty != 0.00
            ):
                raise ValidationError(
                    _(
                        "Product '%(product)s' cannot be sold below the "
                        "Lowest Allowed Price (%(price)s)."
                    ) % {
                        'product': product.display_name,
                        'price': lowest_price,
                    }
                )

    def _get_custom_invoiced_qty(self):
        self.ensure_one()

        invoiced_qty = 0.0

        invoice_lines = self.invoice_lines.filtered(
            lambda line:
                line.move_id
                and line.move_id.state != 'cancel'
                and line.move_id.move_type in ('out_invoice', 'out_refund')
        )

        for invoice_line in invoice_lines:
            qty = invoice_line.product_uom_id._compute_quantity(
                invoice_line.quantity,
                self.product_uom
            )

            if invoice_line.move_id.move_type == 'out_refund':
                invoiced_qty -= qty
            else:
                invoiced_qty += qty

        return invoiced_qty

    def _get_remaining_delivery_qty(self):
        self.ensure_one()

        invoiced_qty = self._get_custom_invoiced_qty()
        remaining_qty = self.qty_delivered - invoiced_qty

        if float_compare(
            remaining_qty,
            0.0,
            precision_rounding=self.product_uom.rounding,
        ) <= 0:
            return 0.0

        return remaining_qty

    def _prepare_invoice_line(self, **optional_values):
        vals = super()._prepare_invoice_line(**optional_values)

        if self.product_uom_qty == 0 and self.qty_delivered > 0:
            remaining_qty = self._get_remaining_delivery_qty()

            vals['quantity'] = remaining_qty

        return vals


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    def _get_invoiceable_lines(self, final=False):
        lines = super()._get_invoiceable_lines(final=final)

        extra_lines = self.env['sale.order.line']

        for order in self:
            candidate_lines = order.order_line.filtered(
                lambda line:
                    not line.display_type
                    and not line.is_downpayment
                    and line.product_id
                    and line.product_uom_qty == 0
                    and line.qty_delivered > 0
                    and float_compare(
                        line._get_remaining_delivery_qty(),
                        0.0,
                        precision_rounding=line.product_uom.rounding,
                    ) > 0
            )

            extra_lines |= candidate_lines

        valid_lines = lines.filtered(
            lambda line:
                not (
                    not line.display_type
                    and line.product_uom_qty == 0
                    and line.qty_delivered > 0
                    and float_compare(
                        line._get_remaining_delivery_qty(),
                        0.0,
                        precision_rounding=line.product_uom.rounding,
                    ) <= 0
                )
        )

        return valid_lines | extra_lines