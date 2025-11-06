# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _order_revised_count(self):
        for sale_rec in self:
            order_revised_count = self.search(
                [('parent_saleorder_id', '=', sale_rec.id)])
            sale_rec.order_revised_count = len(order_revised_count)

    name = fields.Char(string='Order Reference', required=True, copy=False,
                       readonly=True, index=True, default='New')
    parent_saleorder_id = fields.Many2one(
        'sale.order', 'Parent SaleOrder', copy=False)

    order_revised_count = fields.Integer(
        '# of Orders Revised', compute='_order_revised_count', copy=False)

    so_number = fields.Integer('SO Number', copy=False, default=1)
    id_number = fields.Char('id Char', copy=False)
    char_name = fields.Char('Char Name', copy=False)
    state = fields.Selection(selection_add=[
        ('draft_quote', 'Revised Quotation'),
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('revised', 'Revised Order'),
        ('sale', 'Sale Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True,
        tracking=True, default='draft')

    order_count = fields.Integer(
        '# of Orders Revised', compute='_order_revised_count2', copy=False)
    is_new = fields.Boolean()
    revised_ref_id = fields.Many2one('sale.order', 'Revised Reference', copy=False)

    def _order_revised_count2(self):
        count = self.env['sale.order'].search_count([('char_name', '=', self.name)])
        self.order_count = count

    def act_action_sale_order_revised2(self):
        return {
            'name': _('Quotation'),
            'domain': [('char_name', '=', self.name)],
            'view_type': 'form',
            'res_model': 'sale.order',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    sale_order_count = fields.Integer(
        '# of Orders Revised', compute='_order_sale_order_count2', copy=False)

    def _order_sale_order_count2(self):
        count = self.env['sale.order'].search_count([('name', '=', self.char_name)])
        self.sale_order_count = count

    def act_action_sale_order_revised(self):
        return {
            'name': _('Quotation'),
            'domain': [('name', '=', self.char_name)],
            'view_type': 'form',
            'res_model': 'sale.order',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def set_so(self):
        for rec in self:
            sale_order = self.env['sale.order'].search([('name', '=', rec.char_name)])
            sale_order.order_line = [(5, 0, 0)]
            lines_vals = []
            for line in rec.order_line:
                lines_vals.append((0, 0, {
                        'name': line.name,
                        'product_id': line.product_id.id,
                        'price_unit': line.price_unit,
                        'product_uom_qty': line.product_uom_qty,
                        'price_subtotal': line.price_subtotal,
                        'customer_lead': line.customer_lead,
                        'tax_id': [(6, 0, line.tax_id.ids)] if line.tax_id.ids else False,
                    }))

            sale_order.write({
                'revised_ref_id': rec.id,
                'partner_id': rec.partner_id.id,
                'currency_id': rec.currency_id.id,
                'sale_order_template_id': rec.sale_order_template_id.id,
                'pricelist_id': rec.pricelist_id.id,
                'payment_term_id': rec.payment_term_id.id,
                'order_line': lines_vals,
                'date_order': rec.date_order,
                'validity_date': rec.validity_date,
            })

    def so_revision_quote(self):
        for cur_rec in self:
            if not cur_rec.origin:
                origin_name = cur_rec.name
                cur_rec.origin = cur_rec.name
            else:
                origin_name = cur_rec.origin

            cur_rec.char_name = origin_name
            vals = {
                'name': cur_rec.name,
                'state': 'draft',
                'is_new': True,
                'parent_saleorder_id': cur_rec.id,
            }
            cur_rec.copy(default=vals)
            cur_rec.state = 'revised'

            sale_order = self.env['sale.order'].search([('char_name', '=', self.name)])
            max = 0
            for order in sale_order:
                if order.so_number > max:
                    max = order.so_number
            if len(sale_order) == 1:
                cur_rec.name = str('RSO' + str(max) + "_" + origin_name)
                cur_rec.so_number = max
            else:
                cur_rec.name = str('RSO' + str(max + 1) + "_" + origin_name)
                cur_rec.so_number = max + 1

    def _action_confirm(self):
        sup_rec = super(SaleOrder, self)._action_confirm()
        child_id = self.search(
            [('parent_saleorder_id', '=', self.id)], order="create_date desc",
            limit=1)
        if child_id:
            child_id.name = self.name

        sale_order = self.env['sale.order'].search([('char_name', '=', self.name)])
        for order in sale_order:
            if order.state == "revised":
                order.state = 'done'
        return sup_rec
