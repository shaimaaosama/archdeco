# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    sh_pricelist_ids = fields.Many2many(
        'product.pricelist', 'res_users_product_pricelist_rel', string='Price List')


class PricelistInherit(models.Model):
    _inherit = 'product.pricelist'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if self.env.user.sh_pricelist_ids.ids:
            args.append(('id', 'in', self.env.user.sh_pricelist_ids.ids))
        return super(PricelistInherit, self).name_search(
            name=name,
            args=args,
            operator=operator,
            limit=limit,
        )

