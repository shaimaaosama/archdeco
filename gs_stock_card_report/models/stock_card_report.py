# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class GsStockCardReport(models.Model):
    _name = 'gs.stock.card.report'
    _description = 'Stock Card Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', 'Product', required=True)
    report_line_ids = fields.One2many('gs.stock.card.report.line', 'link_id')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                location_customer = self.env.ref('stock.stock_location_customers')
                location_supplier = self.env.ref('stock.stock_location_suppliers')
                location_customer_id = self.env['stock.move.line'].search(
                    [('product_id', '=', rec.product_id.id), ('location_id', '=', location_customer.id)])  # sales OUT
                location_dest_customer_id = self.env['stock.move.line'].search([('product_id', '=', rec.product_id.id),
                                                                                ('location_dest_id', '=',
                                                                                 location_customer.id)])  # IN customer

                lines = [(5, 0, 0)]
                for line in location_customer_id:
                    val = {
                        'link_id': rec.id,
                        'date': line.date,
                        'name': line.reference,
                        'sales_in': line.qty_done,
                    }
                    lines.append((0, 0, val))
                    rec.report_line_ids = lines
                for line in location_dest_customer_id:
                    val = {
                        'link_id': rec.id,
                        'date': line.date,
                        'name': line.reference,
                        'sales_out': line.qty_done,
                    }
                    lines.append((0, 0, val))
                    rec.report_line_ids = lines

                location_vendor_id = self.env['stock.move.line'].search(
                    [('product_id', '=', rec.product_id.id), ('location_id', '=', location_supplier.id)])  # IN Vendor
                location_dest_vendor_id = self.env['stock.move.line'].search([('product_id', '=', rec.product_id.id), (
                'location_dest_id', '=', location_supplier.id)])  # IN Vendor

                for line in location_vendor_id:
                    val = {
                        'link_id': rec.id,
                        'date': line.date,
                        'name': line.reference,
                        'purchase_in': line.qty_done,
                    }
                    lines.append((0, 0, val))
                    rec.report_line_ids = lines
                for line in location_dest_vendor_id:
                    val = {
                        'link_id': rec.id,
                        'date': line.date,
                        'name': line.reference,
                        'purchase_out': line.qty_done,
                    }
                    lines.append((0, 0, val))
                    rec.report_line_ids = lines


class GsStockCardReportLine(models.Model):
    _name = 'gs.stock.card.report.line'
    _order = 'date ASC'

    link_id = fields.Many2one('gs.stock.card.report')
    date = fields.Date(string='Date')
    name = fields.Char(string='Name')
    sales_in = fields.Float(string='Sales In', digits='Product Unit of Measure')
    sales_out = fields.Float(string='Sales Out', digits='Product Unit of Measure')
    sales_balance = fields.Float(string='Balance', digits='Product Unit of Measure')
    purchase_in = fields.Float(string='Purchase In', digits='Product Unit of Measure')
    purchase_out = fields.Float(string='Purchase Out', digits='Product Unit of Measure')


class ProductProductInherit(models.Model):
    _inherit = 'product.template'

    order_limit = fields.Float(string='Order Limit')
    lead_time = fields.Float(string='Lead Time')
    Product_entry_date = fields.Date(string='Product Entry Date', )
