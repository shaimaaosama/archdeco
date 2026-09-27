# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class TransferReturnPickingLine(models.TransientModel):
    _name = "transfer.return.line"
    _rec_name = 'product_id'
    _description = 'Return Picking Line'

    product_id = fields.Many2one('product.product', string="Product", required=True, domain="[('id', '=', product_id)]")
    quantity = fields.Float("Quantity", digits='Product Unit of Measure', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', related='product_id.uom_id')
    wizard_id = fields.Many2one('transfer.return.picking', string="Wizard")
    move_id = fields.Many2one('stock.move', "Move")

    sh_sec_uom = fields.Many2one(
        "uom.uom",
        'Secondary UOM',
        readonly=False
    )
    sh_sec_qty = fields.Float(
        "Secondary Qty",
        digits='Product Unit of Measure',
        readonly=False
    )

    sh_is_secondary_unit = fields.Boolean(
        "Related Sec Unit", related="product_id.sh_is_secondary_unit"


    )


class TransferReturnPicking(models.TransientModel):
    _name = 'transfer.return.picking'
    _description = 'Return Picking'

    @api.model
    def default_get(self, fields):
        res = super(TransferReturnPicking, self).default_get(fields)
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'stock.internal.transfer':
            if len(self.env.context.get('active_ids', list())) > 1:
                raise UserError(_("You may only return one picking at a time."))
            transfer = self.env['stock.internal.transfer'].browse(self.env.context.get('active_id'))
            if transfer.exists():
                res.update({'transfer_id': transfer.id})
        return res

    transfer_id = fields.Many2one('stock.internal.transfer', string="Transfer",)

    picking_id = fields.Many2one('stock.picking')
    product_return_moves = fields.One2many('transfer.return.line', 'wizard_id', 'Moves')
    move_dest_exists = fields.Boolean('Chained Move Exists', readonly=True)
    original_location_id = fields.Many2one('stock.location')
    parent_location_id = fields.Many2one('stock.location')
    company_id = fields.Many2one(related='picking_id.company_id')
    location_id = fields.Many2one(
        'stock.location', 'Return Location',
        )

    @api.onchange('transfer_id')
    def _onchange_transfer_id(self):
        move_dest_exists = False
        product_return_moves = [(5,)]
        # if self.transfer_id and self.transfer_id.state != 'done':
        #     raise UserError(_("You may only return Done pickings."))

        # In case we want to set specific default values (e.g. 'to_refund'), we must fetch the
        # default values for creation.
        line_fields = [f for f in self.env['transfer.return.line']._fields.keys()]
        product_return_moves_data_tmpl = self.env['transfer.return.line'].default_get(line_fields)

        for move in self.transfer_id.line_ids:
            product_return_moves_data = dict(product_return_moves_data_tmpl)
            product_return_moves_data.update(self._prepare_stock_return_picking_line_vals_from_move(move))
            product_return_moves.append((0, 0, product_return_moves_data))
        if self.transfer_id and not product_return_moves:
            raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)."))
        if self.transfer_id:
            self.product_return_moves = product_return_moves
            self.location_id = self.transfer_id.source_warehouse_id.lot_stock_id.id

    @api.model
    def _prepare_stock_return_picking_line_vals_from_move(self, stock_move):
        quantity = stock_move.product_qty
        quantity = float_round(quantity, precision_rounding=stock_move.product_id.uom_id.rounding)
        return {
            'product_id': stock_move.product_id.id,
            'quantity': quantity,
            'move_id': stock_move.id,
            'sh_sec_uom': stock_move.sh_sec_uom.id,
            'sh_sec_qty': stock_move.sh_sec_qty,
            'sh_is_secondary_unit': stock_move.sh_is_secondary_unit,
        }

    def _prepare_move_default_values(self, return_line, new_picking):
        vals = {
            'product_id': return_line.product_id.id,
            'product_uom_qty': return_line.quantity,
            'product_uom': return_line.product_id.uom_id.id,
            'picking_id': new_picking.id,
            'state': 'draft',
            'date': fields.Datetime.now(),
            'location_id': return_line.move_id.location_dest_id.id,
            'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
            'picking_type_id': new_picking.picking_type_id.id,
            'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
            'origin_returned_move_id': return_line.move_id.id,
            'procure_method': 'make_to_stock',
        }
        return vals

    def create_returns(self):
        for tf in self:
            if 'active_ids' in self._context:
                transfer = self.env['stock.internal.transfer'].browse(self._context.get('active_ids')[0])
                company_id = self.env['res.users'].browse(self._uid).company_id.id
                company = self.env['res.company'].browse(company_id)
                type_obj = self.env['stock.picking.type']
                types = type_obj.search([('default_location_dest_id', '=', self.location_id.id), ('code', '=', 'incoming')],limit=1)

                if types:
                    picking_obj = self.env['stock.picking']
                    picking_id = picking_obj.create({
                        'picking_type_id': types.id,
                        'transfer_id': self._context.get('active_ids')[0],
                        'location_id': company.transit_location_id.id,
                        'location_dest_id': transfer.source_warehouse_id.lot_stock_id.id,
                        'company_id': types.company_id.id,
                    })
                else:
                    raise UserError(_('Unable to find destination location in Stock Picking'))

                move_obj = self.env['stock.move']

                for line in tf.product_return_moves:
                    move_obj.create({
                        'name': 'Stock Internal Transfer',
                        'product_id': line.product_id.id,
                        'product_uom': line.uom_id.id,
                        'product_uom_qty': line.quantity,
                        'quantity': line.quantity,
                        'location_id': company.transit_location_id.id,
                        'location_dest_id': transfer.source_warehouse_id.lot_stock_id.id,
                        'picking_id': picking_id.id,
                        'company_id': types.company_id.id,
                    })

                picking_obj = self.env['stock.picking'].browse(picking_id.id)
                picking_obj.action_confirm()
                picking_obj.action_assign()
                picking_obj.button_validate()
                # immediate_transfer_obj = self.env['stock.immediate.transfer'].search([('pick_ids', '=', picking_obj.id)])
                # immediate_transfer_obj.process()
                picking_obj._action_done()

                transfer._get_warehouse_qty()

                # for lines in transfer.line_ids:
                #     lines.qty_warehouse += lines.product_qty

                transfer.state = 'return'