from odoo import api, fields, models
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time, timedelta
import calendar
import io
import base64
from xlwt import easyxf
from odoo.tools.misc import xlwt


class GsStockCardReportWizard(models.TransientModel):
    _name = 'gs.stock.card.report.wizard'
    _description = "Stock Card Report Wizard"

    start_from = fields.Date(string='From')
    start_to = fields.Date(string='To')
    product_ids = fields.Many2many('product.product', string='Product')
    product_categ_ids = fields.Many2many('product.category', string="Category")
    brand_ids = fields.Many2many('product.brand', string='Brand')

    file_name = fields.Char('File Name')
    leave_summary_file = fields.Binary('Stock Card Report')
    leave_report_printed = fields.Boolean('Stock Card Report Printed')

    def action_pdf_wizard(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_from': self.start_from,
                'start_to': self.start_to,
                'product_ids': self.product_ids.ids,
                'product_categ_ids': self.product_categ_ids.ids,
                'brand_ids': self.brand_ids.ids,
                'file_name': self.file_name,
                'leave_summary_file': self.leave_summary_file,
                'leave_report_printed': self.leave_report_printed,
            },
        }
        return self.env.ref('gs_stock_card_report.stock_card_report').report_action(None, data=data)

    def action_html_wizard(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_from': self.start_from,
                'start_to': self.start_to,
                'product_ids': self.product_ids.ids,
                'product_categ_ids': self.product_categ_ids.ids,
                'brand_ids': self.brand_ids.ids,
                'file_name': self.file_name,
                'leave_summary_file': self.leave_summary_file,
                'leave_report_printed': self.leave_report_printed,
            },
        }
        return self.env.ref('gs_stock_card_report.stock_card_report_html').report_action(None, data=data)

    def action_excel_wizard(self):
        data = {
            'start_from': self.start_from,
            'start_to': self.start_to,
            'product_ids': self.product_ids.ids,
            'product_categ_ids': self.product_categ_ids.ids,
            'brand_ids': self.brand_ids.ids,
            'file_name': self.file_name,
            'leave_summary_file': self.leave_summary_file,
            'leave_report_printed': self.leave_report_printed,
        }
        return self.env.ref('gs_stock_card_report.action_stock_card_xlsx_report').report_action(self, data=data)


class StockCardReport(models.AbstractModel):
    _name = 'report.gs_stock_card_report.stock_card_report_view'

    @api.model
    def _get_report_values(self, docids=None, data=None):
        docs = []
        location_customer = self.env.ref('stock.stock_location_customers')
        location_supplier = self.env.ref('stock.stock_location_suppliers')
        location_adjustment = self.env['stock.location'].search([('usage', '=', 'inventory'), ('name', '=', 'Inventory adjustment')])
        location_scrap = self.env['stock.location'].search([('usage', '=', 'inventory'), ('name', '=', 'Scrap')])

        form_data = data['form']
        start_from = datetime.strptime(form_data['start_from'], '%Y-%m-%d').date()
        start_to = datetime.strptime(form_data['start_to'], '%Y-%m-%d').date()

        rd = relativedelta(start_to, start_from)
        available_days = abs((start_to - start_from).days)
        products_domains = [('type', '=', 'product')]
        if data['form']['product_ids']:
            product_ids = data['form']['product_ids']
            products_domains.append(('id', 'in', product_ids))

        if data['form']['product_categ_ids']:
            product_categ_ids = data['form']['product_categ_ids']
            products_domains.append(('categ_id', 'in', product_categ_ids))

        if data['form']['brand_ids']:
            brand_ids = data['form']['brand_ids']
            products_domains.append(('brand_id', 'in', brand_ids))

        products = self.env['product.product'].search(products_domains)

        for product in products:
            domains = ['|', ('location_id', '=', location_customer.id), ('location_dest_id', '=', location_customer.id),('product_id', '=', product.id), ('state', '=', 'done')]
            domains2 = ['|', ('location_id', '=', location_supplier.id), ('location_dest_id', '=', location_supplier.id),('product_id', '=', product.id), ('state', '=', 'done')]
            domains3 = ['|', ('location_id', '=', location_adjustment.id), ('location_dest_id', '=', location_adjustment.id),('product_id', '=', product.id), ('state', '=', 'done')]
            domains4 = [('location_dest_id', '=', location_scrap.id), ('product_id', '=', product.id)]

            domains5 = [('location_id', '=', location_customer.id), ('product_id', '=', product.id), ('state', 'not in', ['done', 'cancel'])]
            domains6 = [('location_id', '=', location_supplier.id), ('product_id', '=', product.id), ('state', 'not in', ['done', 'cancel'])]
            domains7 = [('location_id', '=', location_adjustment.id), ('product_id', '=', product.id), ('state', 'not in', ['done', 'cancel'])]
            domains8 = [('location_dest_id', '=', location_scrap.id), ('product_id', '=', product.id), ('state', 'not in', ['done', 'cancel'])]

            domains9 = [('location_dest_id', '=', location_customer.id), ('product_id', '=', product.id), ('state', 'not in', ['done', 'cancel'])]
            domains10 = [('location_dest_id', '=', location_supplier.id), ('product_id', '=', product.id), ('state', 'not in', ['done', 'cancel'])]
            domains11 = [('location_dest_id', '=', location_adjustment.id), ('product_id', '=', product.id), ('state', 'not in', ['done', 'cancel'])]

            if data['form']['start_from'] and data['form']['start_to']:
                domains.append(('date', '>=', data['form']['start_from']))
                domains.append(('date', '<=', data['form']['start_to']))

                domains2.append(('date', '>=', data['form']['start_from']))
                domains2.append(('date', '<=', data['form']['start_to']))

                domains3.append(('date', '>=', data['form']['start_from']))
                domains3.append(('date', '<=', data['form']['start_to']))

                domains4.append(('date', '>=', data['form']['start_from']))
                domains4.append(('date', '<=', data['form']['start_to']))

                domains5.append(('date', '>=', data['form']['start_from']))
                domains5.append(('date', '<=', data['form']['start_to']))

                domains6.append(('date', '>=', data['form']['start_from']))
                domains6.append(('date', '<=', data['form']['start_to']))

                domains7.append(('date', '>=', data['form']['start_from']))
                domains7.append(('date', '<=', data['form']['start_to']))

                domains8.append(('date', '>=', data['form']['start_from']))
                domains8.append(('date', '<=', data['form']['start_to']))

                domains9.append(('date', '>=', data['form']['start_from']))
                domains9.append(('date', '<=', data['form']['start_to']))

                domains10.append(('date', '>=', data['form']['start_from']))
                domains10.append(('date', '<=', data['form']['start_to']))

                domains11.append(('date', '>=', data['form']['start_from']))
                domains11.append(('date', '<=', data['form']['start_to']))

            location_customer_id = self.env['stock.move.line'].search(domains)
            location_vendor_id = self.env['stock.move.line'].search(domains2)
            location_adjustment_id = self.env['stock.move.line'].search(domains3)
            location_scrap_id = self.env['stock.move.line'].search(domains4)
            opening_balance_product = self.env['stock.move.line'].search([('date', '<', data['form']['start_from']), ('product_id', '=', product.id)])

            location_customer_id_new = self.env['stock.move.line'].search(domains5)
            location_vendor_id_new = self.env['stock.move.line'].search(domains6)
            location_adjustment_id_new = self.env['stock.move.line'].search(domains7)
            location_scrap_id_new = self.env['stock.move.line'].search(domains8)

            location_customer_id_new_ven = self.env['stock.move.line'].search(domains9)
            location_vendor_id_new_ven = self.env['stock.move.line'].search(domains10)
            location_adjustment_id_new_ven = self.env['stock.move.line'].search(domains11)

            sales_in = 0
            sales_out = 0
            purchase_in = 0
            purchase_out = 0
            balance = 0
            opening_balance = 0
            adjustment_in = 0
            adjustment_out = 0
            scrap_out = 0

            sales_in_new = 0
            sales_out_new = 0
            purchase_in_new = 0
            purchase_out_new = 0
            balance_new = 0
            adjustment_in_new = 0
            adjustment_out_new = 0
            scrap_out_new = 0

            total_balance = 0
            reorder_stock = 0
            turn_over = 0
            stock_days = 0

            # sales_in = sum(location_customer_id.mapped('in_qty'))
            # sales_out = - sum(location_customer_id.mapped('out_qty'))
            #
            # purchase_in = sum(location_vendor_id.mapped('in_qty'))
            # purchase_out = - sum(location_vendor_id.mapped('out_qty'))
            #
            # adjustment_in = sum(location_adjustment_id.mapped('in_qty'))
            # adjustment_out = - sum(location_adjustment_id.mapped('out_qty'))
            #
            # scrap_out = - sum(location_scrap_id.mapped('out_qty'))
            #
            # opening_balance += sum(opening_balance_product.mapped('in_qty'))
            # opening_balance += sum(opening_balance_product.mapped('out_qty'))

            for line in location_customer_id:
                sales_in += line.in_qty
                sales_out += -line.out_qty

            for line in location_vendor_id:
                purchase_in += line.in_qty
                purchase_out += -line.out_qty

            for line in location_adjustment_id:
                adjustment_in += line.in_qty
                adjustment_out += -line.out_qty

            for line in location_scrap_id:
                scrap_out += -line.out_qty

            for line in opening_balance_product:
                opening_balance += line.in_qty
                opening_balance += line.out_qty
            balance = opening_balance + purchase_in + adjustment_in + sales_in - sales_out - purchase_out - adjustment_out - scrap_out

            # sales_in_new = sum(location_customer_id_new.mapped('product_uom_qty'))
            # sales_out_new = - sum(location_customer_id_new_ven.mapped('product_uom_qty'))
            #
            # purchase_in_new = sum(location_vendor_id_new.mapped('product_uom_qty'))
            # purchase_out_new = - sum(location_vendor_id_new_ven.mapped('product_uom_qty'))
            #
            # adjustment_in_new = sum(location_adjustment_id_new.mapped('product_uom_qty'))
            # adjustment_out_new = - sum(location_adjustment_id_new_ven.mapped('product_uom_qty'))
            #
            # scrap_out_new = - sum(location_scrap_id_new.mapped('product_uom_qty'))
            for line in location_customer_id_new:
                sales_in_new += line.product_uom_qty

            for line in location_vendor_id_new:
                purchase_in_new += line.product_uom_qty

            for line in location_adjustment_id_new:
                adjustment_in_new += line.product_uom_qty

            for line in location_scrap_id_new:
                scrap_out_new += line.product_uom_qty

            for line in location_customer_id_new_ven:
                sales_out_new += line.product_uom_qty

            for line in location_vendor_id_new_ven:
                purchase_out_new += line.product_uom_qty

            for line in location_adjustment_id_new_ven:
                adjustment_out_new += line.product_uom_qty

            balance_new = purchase_in_new + adjustment_in_new + sales_in_new - sales_out_new - purchase_out_new - adjustment_out_new - scrap_out_new

            if sales_out != 0:
                total_balance = balance + balance_new
                reorder_stock = (sales_out - sales_in) / available_days * product.order_limit * product.lead_time
                if total_balance != 0:
                    turn_over = (sales_out - sales_in) / total_balance
                if turn_over != 0:
                    stock_days = available_days / turn_over

            docs.append({
                'product_id': product.name,
                'order_limit': product.order_limit,
                'lead_time': product.lead_time,
                'Product_entry_date': product.Product_entry_date,
                'opening_balance': opening_balance,
                'sales_in': sales_in,
                'sales_out': sales_out,
                'purchase_in': purchase_in,
                'purchase_out': purchase_out,
                'adjustment_in': adjustment_in,
                'adjustment_out': adjustment_out,
                'scrap_out': scrap_out,
                'balance': balance,


                'sales_in_new': sales_in_new,
                'sales_out_new': sales_out_new,
                'purchase_in_new': purchase_in_new,
                'purchase_out_new': purchase_out_new,
                'adjustment_in_new': adjustment_in_new,
                'adjustment_out_new': adjustment_out_new,
                'scrap_out_new': scrap_out_new,
                'balance_new': balance_new,

                'total_balance': total_balance,
                'reorder_stock': reorder_stock,
                'turn_over': turn_over,
                'stock_days': stock_days,
            })

        return {
            'doc_model': data['model'],
            'start_from': data['form']['start_from'],
            'start_to': data['form']['start_to'],
            'docs': docs,
        }


class SaleOrderXlsxReport(models.AbstractModel):
    _name = 'report.gs_stock_card_report.stock_card_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        location_customer = self.env.ref('stock.stock_location_customers')
        location_supplier = self.env.ref('stock.stock_location_suppliers')
        location_adjustment = self.env['stock.location'].search([('usage', '=', 'inventory'), ('name', '=', 'Inventory adjustment')])
        location_scrap = self.env['stock.location'].search([('usage', '=', 'inventory'), ('name', '=', 'Scrap')])

        # form_data = data['form']
        start_from = datetime.strptime(data['start_from'], '%Y-%m-%d').date()
        start_to = datetime.strptime(data['start_to'], '%Y-%m-%d').date()

        rd = relativedelta(start_to, start_from)
        available_days = abs((start_to - start_from).days)
        sheet = workbook.add_worksheet('')
        bold = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#fffbed', 'border': True})
        title = workbook.add_format(
            {'bold': True, 'align': 'center', 'font_size': 20, 'bg_color': '#f2f2f2', 'border': True})
        date_style = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 14, 'bg_color': '#f2f2f2', 'border': True})
        date_style2 = workbook.add_format({'align': 'center', 'font_size': 12})
        header_row_style = workbook.add_format({'bg_color': '#f2f2f2', 'color': '#000000', 'bold': True, 'align': 'center', 'border': True})
        sheet.merge_range('A1:Y2', 'Forcast Stock Card Report', title)
        money = workbook.add_format({'num_format': '$#,##0.00', 'bg_color': '#ffffff'})
        sheet.merge_range('A4:G4', 'From', date_style)
        sheet.merge_range('A5:G5', data.get('start_from'), date_style2)
        sheet.merge_range('H4:O4', 'To', date_style)
        sheet.merge_range('H5:O5', data.get('start_to'), date_style2)

        # Header row
        sheet.set_column(0, 0, 25)
        sheet.set_column(1, 1, 13)
        sheet.set_column(2, 2, 13)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 13)
        sheet.set_column(5, 5, 13)
        sheet.set_column(6, 6, 13)
        sheet.set_column(7, 7, 13)
        sheet.set_column(8, 8, 13)
        sheet.set_column(9, 9, 13)
        sheet.set_column(10, 10, 13)
        sheet.set_column(11, 11, 13)
        sheet.set_column(12, 12, 13)
        sheet.set_column(13, 13, 13)
        sheet.set_column(14, 14, 13)
        sheet.set_column(15, 15, 13)
        sheet.set_column(16, 16, 13)
        sheet.set_column(17, 17, 13)
        sheet.set_column(18, 18, 13)
        sheet.set_column(19, 19, 15)
        sheet.set_column(20, 20, 13)
        sheet.set_column(21, 21, 13)
        sheet.set_column(22, 22, 13)
        sheet.set_column(23, 23, 13)
        sheet.set_column(23, 24, 13)

        sheet.write(6, 0, 'Product', header_row_style)
        sheet.write(6, 1, 'Entry Date', header_row_style)
        sheet.write(6, 2, 'Lead Time', header_row_style)
        sheet.write(6, 3, 'Order Limit', header_row_style)
        sheet.write(6, 4, 'Opening Balance', header_row_style)
        sheet.merge_range('F7:G7', 'Sales', header_row_style)
        sheet.merge_range('H7:I7', 'Purchase', header_row_style)
        sheet.merge_range('J7:K7', 'Adjustment', header_row_style)
        sheet.write(6, 11, 'Scrap', header_row_style)
        sheet.write(6, 12, 'Balance', header_row_style)
        sheet.merge_range('N7:O7', 'Sales Forcast', header_row_style)
        sheet.merge_range('P7:Q7', 'Purchase Forcast', header_row_style)
        sheet.merge_range('R7:S7', 'Adjustment Forcast', header_row_style)
        sheet.write(6, 19, 'Scrap Forcast', header_row_style)
        sheet.write(6, 20, 'Balance Forcast', header_row_style)
        sheet.write(6, 21, 'Total Balance', header_row_style)
        sheet.write(6, 22, 'Reorder Stock', header_row_style)
        sheet.write(6, 23, 'Turn Over', header_row_style)
        sheet.write(6, 24, 'Stock Days', header_row_style)

        sheet.write(7, 0, '', header_row_style)
        sheet.write(7, 1, '', header_row_style)
        sheet.write(7, 2, '', header_row_style)
        sheet.write(7, 2, '', header_row_style)
        sheet.write(7, 3, '', header_row_style)
        sheet.write(7, 4, 'In', header_row_style)
        sheet.write(7, 5, 'Out', header_row_style)
        sheet.write(7, 6, 'In', header_row_style)
        sheet.write(7, 7, 'Out', header_row_style)
        sheet.write(7, 8, 'In', header_row_style)
        sheet.write(7, 9, 'Out', header_row_style)
        sheet.write(7, 10, '', header_row_style)
        sheet.write(7, 11, '', header_row_style)
        sheet.write(7, 12, 'In', header_row_style)
        sheet.write(7, 13, 'Out', header_row_style)
        sheet.write(7, 14, 'In', header_row_style)
        sheet.write(7, 15, 'Out', header_row_style)
        sheet.write(7, 16, 'In', header_row_style)
        sheet.write(7, 17, 'Out', header_row_style)
        sheet.write(7, 18, '', header_row_style)
        sheet.write(7, 19, '', header_row_style)
        sheet.write(7, 20, '', header_row_style)
        sheet.write(7, 21, '', header_row_style)
        sheet.write(7, 22, '', header_row_style)
        sheet.write(7, 23, '', header_row_style)

        products_domains = [('type', '=', 'product')]
        if data.get('product_ids'):
            product_ids = data.get('product_ids')
            products_domains.append(('id', 'in', product_ids))

        if data.get('product_categ_ids'):
            product_categ_ids = data.get('product_categ_ids')
            products_domains.append(('categ_id', 'in', product_categ_ids))

        if data.get('brand_ids'):
            brand_ids = data.get('brand_ids')
            products_domains.append(('brand_id', 'in', brand_ids))

        products = self.env['product.product'].search(products_domains)
        row = 8
        for product in products:
            domains = ['|', ('location_id', '=', location_customer.id), ('location_dest_id', '=', location_customer.id),
                       ('product_id', '=', product.id), ('state', '=', 'done')]
            domains2 = ['|', ('location_id', '=', location_supplier.id), ('location_dest_id', '=', location_supplier.id),
                        ('product_id', '=', product.id), ('state', '=', 'done')]
            domains3 = ['|', ('location_id', '=', location_adjustment.id),
                        ('location_dest_id', '=', location_adjustment.id), ('product_id', '=', product.id),
                        ('state', '=', 'done')]
            domains4 = [('location_dest_id', '=', location_scrap.id), ('product_id', '=', product.id)]

            domains5 = [('location_id', '=', location_customer.id), ('product_id', '=', product.id),
                        ('state', 'not in', ['done', 'cancel'])]
            domains6 = [('location_id', '=', location_supplier.id), ('product_id', '=', product.id),
                        ('state', 'not in', ['done', 'cancel'])]
            domains7 = [('location_id', '=', location_adjustment.id), ('product_id', '=', product.id),
                        ('state', 'not in', ['done', 'cancel'])]
            domains8 = [('location_dest_id', '=', location_scrap.id), ('product_id', '=', product.id),
                        ('state', 'not in', ['done', 'cancel'])]

            domains9 = [('location_dest_id', '=', location_customer.id), ('product_id', '=', product.id),
                        ('state', 'not in', ['done', 'cancel'])]
            domains10 = [('location_dest_id', '=', location_supplier.id), ('product_id', '=', product.id),
                         ('state', 'not in', ['done', 'cancel'])]
            domains11 = [('location_dest_id', '=', location_adjustment.id), ('product_id', '=', product.id),
                         ('state', 'not in', ['done', 'cancel'])]

            if data.get('start_from') and data.get('start_to'):
                domains.append(('date', '>=', data.get('start_from')))
                domains.append(('date', '<=', data.get('start_to')))

                domains2.append(('date', '>=', data.get('start_from')))
                domains2.append(('date', '<=', data.get('start_to')))

                domains3.append(('date', '>=', data.get('start_from')))
                domains3.append(('date', '<=', data.get('start_to')))

                domains4.append(('date', '>=', data.get('start_from')))
                domains4.append(('date', '<=', data.get('start_to')))

                domains5.append(('date', '>=', data.get('start_from')))
                domains5.append(('date', '<=', data.get('start_to')))

                domains6.append(('date', '>=', data.get('start_from')))
                domains6.append(('date', '<=', data.get('start_to')))

                domains7.append(('date', '>=', data.get('start_from')))
                domains7.append(('date', '<=', data.get('start_to')))

                domains8.append(('date', '>=', data.get('start_from')))
                domains8.append(('date', '<=', data.get('start_to')))

                domains9.append(('date', '>=', data.get('start_from')))
                domains9.append(('date', '<=', data.get('start_to')))

                domains10.append(('date', '>=', data.get('start_from')))
                domains10.append(('date', '<=', data.get('start_to')))

                domains11.append(('date', '>=', data.get('start_from')))
                domains11.append(('date', '<=', data.get('start_to')))

            location_customer_id = self.env['stock.move.line'].search(domains)
            location_vendor_id = self.env['stock.move.line'].search(domains2)
            location_adjustment_id = self.env['stock.move.line'].search(domains3)
            location_scrap_id = self.env['stock.move.line'].search(domains4)
            opening_balance_product = self.env['stock.move.line'].search([('date', '<', data.get('start_from')), ('product_id', '=', product.id)])

            location_customer_id_new = self.env['stock.move.line'].search(domains5)
            location_vendor_id_new = self.env['stock.move.line'].search(domains6)
            location_adjustment_id_new = self.env['stock.move.line'].search(domains7)
            location_scrap_id_new = self.env['stock.move.line'].search(domains8)

            location_customer_id_new_ven = self.env['stock.move.line'].search(domains9)
            location_vendor_id_new_ven = self.env['stock.move.line'].search(domains10)
            location_adjustment_id_new_ven = self.env['stock.move.line'].search(domains11)


            sales_in = 0
            sales_out = 0
            purchase_in = 0
            purchase_out = 0
            balance = 0
            opening_balance = 0
            adjustment_in = 0
            adjustment_out = 0
            scrap_out = 0

            sales_in_new = 0
            sales_out_new = 0
            purchase_in_new = 0
            purchase_out_new = 0
            balance_new = 0
            adjustment_in_new = 0
            adjustment_out_new = 0
            scrap_out_new = 0

            total_balance = 0
            reorder_stock = 0
            turn_over = 0
            stock_days = 0

            for line in location_customer_id:
                sales_in += line.in_qty
                sales_out += -line.out_qty

            for line in location_vendor_id:
                purchase_in += line.in_qty
                purchase_out += -line.out_qty

            for line in location_adjustment_id:
                adjustment_in += line.in_qty
                adjustment_out += -line.out_qty

            for line in location_scrap_id:
                scrap_out += -line.out_qty

            for line in opening_balance_product:
                opening_balance += line.in_qty
                opening_balance += line.out_qty
            balance = opening_balance + purchase_in + adjustment_in + sales_in - sales_out - purchase_out - adjustment_out - scrap_out

            for line in location_customer_id_new:
                sales_in_new += line.product_uom_qty

            for line in location_vendor_id_new:
                purchase_in_new += line.product_uom_qty

            for line in location_adjustment_id_new:
                adjustment_in_new += line.product_uom_qty

            for line in location_scrap_id_new:
                scrap_out_new += line.product_uom_qty

            for line in location_customer_id_new_ven:
                sales_out_new += line.product_uom_qty

            for line in location_vendor_id_new_ven:
                purchase_out_new += line.product_uom_qty

            for line in location_adjustment_id_new_ven:
                adjustment_out_new += line.product_uom_qty

            balance_new = purchase_in_new + adjustment_in_new + sales_in_new - sales_out_new - purchase_out_new - adjustment_out_new - scrap_out_new

            if sales_out != 0:
                total_balance = balance + balance_new
                reorder_stock = (sales_out - sales_in) / available_days * product.order_limit * product.lead_time
                if total_balance != 0:
                    turn_over = (sales_out - sales_in) / total_balance
                if turn_over != 0:
                    stock_days = available_days / turn_over

            sheet.write(row, 0, product.name)
            sheet.write(row, 1, product.Product_entry_date, workbook.add_format({"num_format": "dd/mm/yy"}))
            sheet.write(row, 2, product.lead_time)
            sheet.write(row, 3, product.order_limit)
            sheet.write(row, 4, opening_balance)
            sheet.write(row, 5, sales_in)
            sheet.write(row, 6, sales_out)
            sheet.write(row, 7, purchase_in)
            sheet.write(row, 8, purchase_out)
            sheet.write(row, 9, adjustment_in)
            sheet.write(row, 10, adjustment_out)
            sheet.write(row, 11,scrap_out)
            sheet.write(row, 12, balance)
            sheet.write(row, 13, sales_in_new)
            sheet.write(row, 14, sales_out_new)
            sheet.write(row, 15, purchase_in_new)
            sheet.write(row, 16, purchase_out_new)
            sheet.write(row, 17, adjustment_in_new)
            sheet.write(row, 18, adjustment_out_new)
            sheet.write(row, 19, scrap_out_new)
            sheet.write(row, 20, balance_new)
            sheet.write(row, 21, total_balance)
            sheet.write(row, 22, reorder_stock)
            sheet.write(row, 23, turn_over)
            sheet.write(row, 24, stock_days)

            row += 1
        for wizard in self:
            fp = io.BytesIO()
            workbook.save(fp)
            excel_file = base64.encodestring(fp.getvalue())
            wizard.leave_summary_file = excel_file
            wizard.file_name = 'Contracts Status Report.xls'
            wizard.leave_report_printed = True
            fp.close()
            return {
                'view_mode': 'form',
                'res_id': wizard.id,
                'res_model': 'contracts.status.report.wizard',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
                'context': self.env.context,
                'target': 'new',
            }