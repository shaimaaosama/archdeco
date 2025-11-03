# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GsGetLocationDataWizard(models.TransientModel):
    _name = "get.stock.moves.data.wizard"

    location_ids = fields.Many2many('stock.location', string='Location',)
    location_dest_ids = fields.Many2many('stock.location', 'location_dest_ids02', 'location_dest_ids002', 'location_dest_ids0002', string='To', )
    partner_ids = fields.Many2many('res.partner', string='Partner')
    product_ids = fields.Many2many('product.product', string="Product")
    company_ids = fields.Many2many('res.company', string='Companies')
    company_id = fields.Many2one('res.company', required="1", default=lambda self: self.env.user.company_id)
    start_date = fields.Date(string="Start Date",)
    end_date = fields.Date(string="End Date" )

    @api.onchange('location_ids')
    def domain_location_ids(self):
        return {'domain': {'location_ids': [('id', 'in', self.env.user.stock_location_ids.ids)]}}

    def action_get_data(self):
        view = self.env.ref('stock.view_move_tree')
        domain = []
        if self.location_ids:
            domain += ['|', ("location_id", "in", self.location_ids.ids), ("location_dest_id", "in", self.location_ids.ids)]
        if self.company_id:
            domain += [("company_id", "=", self.company_id.id)]
        if self.partner_ids:
            domain += [('partner_id', 'in', self.partner_ids.ids)]
        if self.product_ids:
            domain += [('product_id', 'in', self.product_ids.ids)]
        if self.start_date:
            domain += [('date', '>=', self.start_date)]
        if self.end_date:
            domain += [('date', '<=', self.end_date)]

        return {
            'name': _('Stock Moves'),
            'domain': domain,

            'view_type': 'form',
            'res_model': 'stock.move',
            'view_id': view.id,
            'view_mode': 'tree',
            'type': 'ir.actions.act_window',
        }