# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    sh_pricelist_ids = fields.Many2many(
        'product.pricelist', 'res_users_product_pricelist_rel', string='Price List')


class PricelistInherit(models.Model):
    _inherit = 'product.pricelist'

    # @api.model
    # def _search(self, args, offset=0, limit=None, order=None):
    #     if self.env.user.sh_pricelist_ids.ids:
    #         args.append(('id', 'in', self.env.user.sh_pricelist_ids.ids))
    #     res = super(PricelistInherit, self)._search(args, offset=offset, limit=limit,
    #                                                 order=order)
    #     return res

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
    #     args = args or []
    #
    #     # Get the current user
    #     model = self.env.context.get('active_model')
    #     print('Ahmed123456', self._name)
    #     user = self.env.user
    #
    #     # Restrict to analytic accounts the user owns
    #     allowed_ids = user.sh_pricelist_ids.ids
    #
    #     # Only keep search results in those IDs
    #     if allowed_ids:
    #         args += [('id', 'in', allowed_ids)]
    #     else:
    #         # If the user has none, return empty
    #         return []
    #
    #     # If name contains something, Odoo will automatically handle the matching
    #     # on rec_name (usually name field) + our args.
    #     return super(PricelistInherit, self).name_search(
    #         name=name,
    #         args=args,
    #         operator=operator,
    #         limit=limit,
    #     )

