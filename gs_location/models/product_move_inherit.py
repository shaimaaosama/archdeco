# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GSStockMoveLineInherit(models.Model):
    _inherit = 'stock.move.line'

    in_qty = fields.Float(string='In Qty', compute='_compute_set_product_qty', digits='Product Unit of Measure',)
    out_qty = fields.Float(string='Out Qty', compute='_compute_set_product_qty', digits='Product Unit of Measure',)

    def _compute_set_product_qty(self):
        for rec in self:
            rec.in_qty = 0
            rec.out_qty = 0
            stock_picking = self.env['stock.picking'].search([('name', '=', rec.reference)])
            if stock_picking.picking_type_id.code == 'incoming':
                rec.in_qty = rec.qty_done
            elif stock_picking.picking_type_id.code == 'outgoing':
                rec.out_qty = - rec.qty_done

            if rec.in_qty == 0 and rec.out_qty == 0:
                if rec.location_id.usage == 'inventory':
                    rec.in_qty = rec.qty_done
                elif rec.location_dest_id.usage == 'inventory':
                    rec.out_qty = - rec.qty_done