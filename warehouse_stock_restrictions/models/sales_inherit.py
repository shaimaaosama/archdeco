# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class SaleInherit(models.Model):
    _inherit = 'sale.order'

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])
        return {'domain': {'warehouse_id': [('id', 'in', res_user.warehouse_restrictions_ids.ids)]}}