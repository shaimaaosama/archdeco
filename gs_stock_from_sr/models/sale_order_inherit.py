# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools.misc import format_date, DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
from odoo.exceptions import AccessError, UserError, ValidationError


class SaleOrderInherit(models.AbstractModel):
    _inherit = 'sale.order'
    
    delivery_order = fields.Char(string='Delivery Orders', compute="_get_delivery", store=True)

    is_delivery = fields.Boolean(compute='_compute_is_create_delivery')
    delivered = fields.Boolean()
    confirm_user_id = fields.Many2one('res.users')

    # test
    def _compute_is_create_delivery(self):
        for rec in self:
            rec.is_delivery =False
            picking_ids_qty = 0
            order_line_qty = 0
            if not rec.picking_ids.move_line_ids_without_package:
                rec.delivered = False

            for line in rec.picking_ids.move_line_ids_without_package:
                if line.picking_id.state != 'cancel':
                    picking_ids_qty += line.qty_done
            for line2 in rec.order_line:
                order_line_qty += line2.product_uom_qty

            new_picking_ids_qty = round(picking_ids_qty, 5)
            new_order_line_qty = round(order_line_qty, 5)

            if new_picking_ids_qty == new_order_line_qty:
                rec.is_delivery = True

        # for rec in self:
        #     rec.is_delivery =False
        #     order_line_qty = 0
        #     for line in rec.order_line:
        #         if line.product_uom_qty > 0:
        #             if line.product_uom_qty == line.qty_delivered:
        #                 rec.is_delivery = True
        #         elif line.product_uom_qty < 0 and line.qty_invoiced:
        #             rec.is_delivery = True

            # for line in rec.picking_ids.move_line_ids_without_package:
            #     if line.picking_id.state != 'cancel':
            #         picking_ids_qty += line.qty_done
            # for line2 in rec.order_line:
            #     order_line_qty += line2.product_uom_qty
            # if picking_ids_qty == order_line_qty:
            #     rec.is_delivery = True
            # else:
            #     for line in rec.picking_ids.move_line_ids_without_package:
            #         if line.picking_id.state != 'cancel':
            #             if order_line_qty < 0:
            #                 rec.is_delivery = True

    @api.depends("delivery_count")
    def _get_delivery(self):
        for rec in self:
            if rec.delivery_count > 0:
                rec.delivery_order = 'Done'
            else:
                rec.delivery_order = 'No Delivery'

    def action_confirm(self):
        self.confirm_user_id = self.env.user.id
        # if self._get_forbidden_state_confirm() & set(self.mapped('state')):
        #     raise UserError(_(
        #         'It is not allowed to confirm an order in the following states: %s'
        #     ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write(self._prepare_confirmation_values())

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        context = self._context.copy()
        context.pop('default_name', None)

        # self.with_context(context)._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()
        return True

    def create_delivery(self):
        context = self._context.copy()
        context.pop('default_name', None)
        self.with_context(context)._action_confirm()

    def action_create_delivery(self):
        context = self._context.copy()
        context.pop('default_name', None)
        self.with_context(context)._action_confirm()
        for line in self.order_line:
            if line.product_uom_qty < 0:
                self.delivered = True
