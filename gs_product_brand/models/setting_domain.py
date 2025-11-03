# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CustomBrandForUsers(models.Model):
    _inherit = 'res.users'

    custom_brand_id = fields.Many2many(comodel_name="product.brand", string="Brand Access",
                                       readonly=False)
    # compute = '_compute_func',
    # @api.onchange('name')

    # @api.depends('name')
    # def _compute_func(self):
    #     for rec in self:
    #         # user = self.env.user
    #         # print('user', user.id)
    #         if self.env.user.has_group('sales_team.group_sale_manager'):
    #             # print('user'*20)
    #             # print('users_g33', rec.custom_brand_id.id)
    #             # users_admin = self.env['res.users'].search(
    #             #     [('groups_id', 'in', [self.env.ref('sales_team.group_sale_manager').id])])
    #             # print('users_g', users_admin)
    #             # print('users_g122', rec.custom_brand_id.id)
    #             # if users_admin:
    #             all_brands = self.env['product.brand'].search([])
    #             print('all_brands', all_brands)
    #             print('all_brands2', all_brands.ids)
    #             rec.custom_brand_id = all_brands.ids
    #         # else:
    #         #     print('else' * 9)
    #         #     rec.custom_brand_id = rec.custom_brand_id