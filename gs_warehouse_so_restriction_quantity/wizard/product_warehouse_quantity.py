# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _


class SaleProductWarehouseQuantity(models.TransientModel):
    _name = "sale.product.warehouse.quantity"
    _description = "Sales Product Warehouse Quantity"

    def default_warehouse_quantity(self):
        if self.env.context.get('active_model', '') == 'sale.order.line':
            ids = self.env.context['active_ids']
            order_lines = self.env['sale.order.line'].browse(ids)

            for line in order_lines:
                warehouse_quantity_text = ''
                quant_ids = self.env['stock.quant'].sudo().search(
                    [('product_id', '=', line.product_id.id), ('location_id.usage', '=', 'internal')])
                t_warehouses = {}
                for quant in quant_ids:
                    if quant.location_id:
                        if quant.location_id not in t_warehouses:
                            t_warehouses.update({quant.location_id: 0})
                        t_warehouses[quant.location_id] += quant.quantity

                tt_warehouses = {}
                for location in t_warehouses:
                    warehouse = False
                    location1 = location
                    while (not warehouse and location1):
                        warehouse_id = self.env['stock.warehouse'].sudo().search([('lot_stock_id', '=', location1.id)])
                        if len(warehouse_id) > 0:
                            warehouse = True
                        else:
                            warehouse = False
                        location1 = location1.location_id
                    if warehouse_id:
                        if warehouse_id.name not in tt_warehouses:
                            tt_warehouses.update({warehouse_id.name: 0})
                        tt_warehouses[warehouse_id.name] += t_warehouses[location]
                warehouse_qty_lines = []
                for item in tt_warehouses:
                    if tt_warehouses[item] != 0:
                        warehouse_quantity_text = warehouse_quantity_text + ' ** ' + item + ': ' + str(
                            tt_warehouses[item])
                        if line.product_uom_qty < tt_warehouses[item]:
                            warehouse_qty_lines.append({'name': item, 'qty': tt_warehouses[item]})
                        else:
                            continue
                return warehouse_qty_lines

    warehouse_qty_lines = fields.Many2many('warehouse.quantity.lines', string="Quantity Per WH", default=default_warehouse_quantity)


class SaleProductWarehouseQuantityLines(models.TransientModel):
    _name = "warehouse.quantity.lines"

    name = fields.Char('Warehouse',readonly=1)
    qty = fields.Char('Quantity',readonly=1)
