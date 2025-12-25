# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class ReturnPickingLineInherit(models.TransientModel):
    _inherit = "stock.return.picking.line"

    sh_sec_qty = fields.Float(
        "Secondary Qty",
        digits='Product Unit of Measure'
    )

    sh_sec_uom = fields.Many2one(
        "uom.uom",
        'Secondary UOM',
        related="product_id.sh_secondary_uom",
        store=True,
        copy=False
    )

    sh_is_secondary_unit = fields.Boolean(
        "Related Sec Unit",
        related="product_id.sh_is_secondary_unit"
    )

    @api.onchange('quantity')
    def onchange_product_uom_done_qty_sh_move_line(self):
        if self and self.sh_is_secondary_unit and self.sh_sec_uom:
            self.sh_sec_qty = self.uom_id._compute_quantity(
                self.quantity,
                self.sh_sec_uom
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
        if self and self.sh_is_secondary_unit and self.uom_id:
            self.quantity = self.sh_sec_uom._compute_quantity(
                self.sh_sec_qty, self.uom_id
            )


class ShStockMove(models.Model):
    _inherit = "stock.move"

    sh_sec_qty = fields.Float(
        "Secondary Qty",
        digits='Product Unit of Measure',
        store=True,
        copy=False
    )
    sh_sec_done_qty = fields.Float(
        "Secondary Done Qty",
        digits='Product Unit of Measure',
        store=True,
        copy=False
    )
    sh_sec_uom = fields.Many2one(
        "uom.uom",
        'Secondary UOM',
        related="product_id.sh_secondary_uom",
        store=True,
        copy=False
    )
    sh_is_secondary_unit = fields.Boolean(
        "Related Sec Unit",
        related="product_id.sh_is_secondary_unit",
        store=True,
        copy=False
    )

    @api.onchange('quantity')
    def onchange_product_uom_done_qty_sh(self):
        if self and self.sh_is_secondary_unit and self.sh_sec_uom:
            self.sh_sec_done_qty = self.product_uom._compute_quantity(
                self.quantity,
                self.sh_sec_uom
            )
        # float_num = self.sh_sec_done_qty - int(self.sh_sec_done_qty)
        # int_num = int(self.sh_sec_done_qty)
        # if float_num > 0.25:
        #     int_num += 1
        #     self.sh_sec_done_qty = int_num
        # else:
        #     self.sh_sec_done_qty = int(self.sh_sec_done_qty)

    @api.onchange('sh_sec_done_qty')
    def onchange_sh_sec_done_qty_sh(self):
        if self and self.sh_is_secondary_unit and self.product_uom:
            self.quantity = self.sh_sec_uom._compute_quantity(
                self.sh_sec_done_qty,
                self.product_uom
            )

    @api.onchange('product_uom_qty', 'product_uom')
    def onchange_product_uom_qty_sh(self):
        if self.sh_is_secondary_unit and self.sh_sec_uom:
            self.sh_sec_qty = self.product_uom._compute_quantity(
                self.product_uom_qty,
                self.sh_sec_uom
            )

    @api.onchange('sh_sec_qty', 'sh_sec_uom')
    def onchange_sh_sec_qty_sh(self):
        if self and self.sh_is_secondary_unit and self.product_uom:
            self.product_uom_qty = self.sh_sec_uom._compute_quantity(
                self.sh_sec_qty,
                self.product_uom
            )

    @api.model
    def create(self, vals):
        res = super(ShStockMove, self).create(vals)
        if res.sale_line_id and res.sale_line_id.sh_is_secondary_unit and res.sale_line_id.sh_sec_uom:
            res.update({
                'sh_sec_uom': res.sale_line_id.sh_sec_uom.id,
                'sh_sec_qty': res.sale_line_id.sh_sec_qty,
            })
        elif res.purchase_line_id and res.purchase_line_id.sh_is_secondary_unit and res.purchase_line_id.sh_sec_uom:
            res.update({
                'sh_sec_uom': res.purchase_line_id.sh_sec_uom.id,
                'sh_sec_qty': res.purchase_line_id.sh_sec_qty,
            })
        return res


class ShStockMoveLine(models.Model):
    _inherit = "stock.move.line"

    sh_sec_qty = fields.Float(
        "Secondary Qty",
        digits='Product Unit of Measure',
        store=True,
        copy=False,
        compute="onchange_product_uom_done_qty_sh_move_line0"

    )
    sh_sec_uom = fields.Many2one(
        "uom.uom",
        'Secondary UOM',
        related="move_id.sh_sec_uom",
        store=True,
        copy=False
    )
    sh_is_secondary_unit = fields.Boolean(
        "Related Sec Unit",
        related="move_id.product_id.sh_is_secondary_unit",
        store=True,
        copy=False
    )

    @api.depends('quantity')
    def onchange_product_uom_done_qty_sh_move_line0(self):
        for rec in self:
            if rec and rec.sh_is_secondary_unit and rec.sh_sec_uom:
                rec.sh_sec_qty = rec.product_uom_id._compute_quantity(
                    rec.qty_done,
                    rec.sh_sec_uom
                )
                rec.move_id.sh_sec_done_qty = rec.product_uom_id._compute_quantity(
                    rec.quantity,
                    rec.move_id.sh_sec_uom
                )

            float_num = rec.sh_sec_qty - int(rec.sh_sec_qty)
            int_num = int(rec.sh_sec_qty)
            if float_num > 0.25:
                int_num += 1
                rec.sh_sec_qty = int_num
            else:
                rec.sh_sec_qty = int(rec.sh_sec_qty)

    @api.onchange('sh_sec_qty')
    def onchange_product_sec_done_qty_sh_move_line(self):
        for rec in self:
            if rec and rec.sh_is_secondary_unit and rec.sh_sec_uom:
                rec.quantity = rec.sh_sec_uom._compute_quantity(
                    rec.sh_sec_qty,
                    rec.product_uom_id
                )
                rec.move_id.quantity = rec.sh_sec_qty

    def _get_aggregated_product_quantities(self, **kwargs):
        """ Returns a dictionary of products (key = id+name+description+uom) and corresponding values of interest.

        Allows aggregation of data across separate move lines for the same product. This is expected to be useful
        in things such as delivery reports. Dict key is made as a combination of values we expect to want to group
        the products by (i.e. so data is not lost). This function purposely ignores lots/SNs because these are
        expected to already be properly grouped by line.

        returns: dictionary {product_id+name+description+uom: {product, name, description, qty_done, product_uom}, ...}
        """
        aggregated_move_lines = {}

        def get_aggregated_properties(move_line=False, move=False):
            move = move or move_line.move_id
            uom = move.product_uom or move_line.product_uom_id
            name = move.product_id.display_name
            description = move.description_picking
            if description == name or description == move.product_id.name:
                description = False
            product = move.product_id
            line_key = f'{product.id}_{product.display_name}_{description or ""}_{uom.id}'
            return (line_key, name, description, uom)

        # Loops to get backorders, backorders' backorders, and so and so...
        backorders = self.env['stock.picking']
        pickings = self.picking_id
        while pickings.backorder_ids:
            backorders |= pickings.backorder_ids
            pickings = pickings.backorder_ids

        for move_line in self:
            if kwargs.get('except_package') and move_line.result_package_id:
                continue
            line_key, name, description, uom = get_aggregated_properties(move_line=move_line)

            qty_done = move_line.product_uom_id._compute_quantity(move_line.qty_done, uom)
            if line_key not in aggregated_move_lines:
                qty_ordered = None
                if backorders and not kwargs.get('strict'):
                    qty_ordered = move_line.move_id.product_uom_qty
                    # Filters on the aggregation key (product, description and uom) to add the
                    # quantities delayed to backorders to retrieve the original ordered qty.
                    following_move_lines = backorders.move_line_ids.filtered(
                        lambda ml: get_aggregated_properties(move=ml.move_id)[0] == line_key
                    )
                    qty_ordered += sum(following_move_lines.move_id.mapped('product_uom_qty'))
                    # Remove the done quantities of the other move lines of the stock move
                    previous_move_lines = move_line.move_id.move_line_ids.filtered(
                        lambda ml: get_aggregated_properties(move=ml.move_id)[0] == line_key and ml.id != move_line.id
                    )
                    qty_ordered -= sum(map(lambda m: m.product_uom_id._compute_quantity(m.qty_done, uom), previous_move_lines))
                aggregated_move_lines[line_key] = {'name': name,
                                                   'description': description,
                                                   'qty_done': qty_done,
                                                   'qty_ordered': qty_ordered or qty_done,
                                                   'quantity': qty_done,
                                                   'product_uom': uom,
                                                   'product_uom_rec': uom,
                                                   'product': move_line.product_id,
                                                   'packaging': move_line.move_id.product_packaging_id,
                                                   'sh_sec_qty': move_line.sh_sec_qty,
                                                   'sh_sec_uom': move_line.sh_sec_uom.name if move_line.sh_sec_uom else '',
                                                   }
            else:
                aggregated_move_lines[line_key]['qty_ordered'] += qty_done
                aggregated_move_lines[line_key]['qty_done'] += qty_done
                aggregated_move_lines[line_key]['quantity'] = aggregated_move_lines[line_key]['qty_done']

        # Does the same for empty move line to retrieve the ordered qty. for partially done moves
        # (as they are splitted when the transfer is done and empty moves don't have move lines).
        if kwargs.get('strict'):
            return aggregated_move_lines
        pickings = (self.picking_id | backorders)
        for empty_move in pickings.move_ids:
            if not (empty_move.state == "cancel" and empty_move.product_uom_qty
                    and float_is_zero(empty_move.quantity, precision_rounding=empty_move.product_uom.rounding)):
                continue
            line_key, name, description, uom = get_aggregated_properties(move=empty_move)

            if line_key not in aggregated_move_lines:
                qty_ordered = empty_move.product_uom_qty
                aggregated_move_lines[line_key] = {
                    'name': name,
                    'description': description,
                    'qty_done': False,
                    'qty_ordered': qty_ordered,
                    'quantity': False,
                    'product_uom': uom,
                    'product': empty_move.product_id,
                    'packaging': empty_move.product_packaging_id,
                }
            else:
                aggregated_move_lines[line_key]['qty_ordered'] += empty_move.product_uom_qty

        return aggregated_move_lines


# class ShStockImmediateTransfer(models.TransientModel):
#     _inherit = 'stock.immediate.transfer'
#
#     def process(self):
#         res = super(ShStockImmediateTransfer, self).process()
#         for picking_ids in self.pick_ids:
#             for moves in picking_ids.move_ids_without_package:
#                 if moves.sh_sec_uom:
#                     moves.sh_sec_done_qty = moves.product_uom._compute_quantity(
#                         moves.product_uom_qty,
#                         moves.sh_sec_uom
#                     )
#                 for move_lines in moves.move_line_ids:
#                     if move_lines.sh_sec_uom:
#                         move_lines.sh_sec_qty = move_lines.product_uom_id._compute_quantity(
#                             move_lines.qty_done,
#                             moves.sh_sec_uom
#                         )
#         return res
