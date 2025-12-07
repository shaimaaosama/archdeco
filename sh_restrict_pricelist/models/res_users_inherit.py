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
    def _search(self, args, offset=0, limit=None, order=None):
        if self.env.user.sh_pricelist_ids.ids:
            args.append(('id', 'in', self.env.user.sh_pricelist_ids.ids))
        res = super(PricelistInherit, self)._search(args, offset=offset, limit=limit,
                                                    order=order)
        return res

