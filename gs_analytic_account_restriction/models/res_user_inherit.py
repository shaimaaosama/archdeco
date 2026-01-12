# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError


class GsResUsersInherit(models.Model):
    _inherit = 'res.users'

    # account_analytic_group_ids = fields.Many2many("account.analytic.group", "account_aa01", "account_aa001", "account_aa0001", string="Analytic Account Groups")
    account_analytic_account_ids = fields.Many2many("account.analytic.account", "account_ana01", "account_ana001",
                                                    "account_ana0001", string="Analytic Accounts")
    # account_analytic_tag_ids = fields.Many2many("account.analytic.tag", "account_tag01", "account_tag001", "account_tag0001", string="Analytic Tags")
    # web_phone_sip_user = fields.Char()
    # web_phone_sip_secret = fields.Char()

    # @api.model
    # def _compute_account_analytic_account(self):
    #     for rec in self:
    #         analytic_account = self.env['account.analytic.account'].search([])
    #         # rec.account_analytic_account_ids = False
    #         for ana in analytic_account:
    #             if self._origin.id in ana.user_ids.ids:
    #                 rec.account_analytic_account_ids = [(4, ana.id)]


class GsAccountAnalyticAccountInherit(models.Model):
    _inherit = 'account.analytic.account'

    user_ids = fields.Many2many("res.users", "gs_user_id_en01", "gs_user_id_en001", "gs_user_id_en0001", string="Users")

    # def default_get(self, field_list):
    #     result = super(GsAccountAnalyticAccountInherit, self).default_get(field_list)
    #     print('ResultAhmed', result)
    #     result.update({
    #         'user_ids': self.env.user.ids,
    #     })
    #     print('ResultAhmed2', result)
    #     return result
    @api.model
    def create(self, vals):
        res = super(GsAccountAnalyticAccountInherit, self).create(vals)
        self.clear_caches()
        self.env.user.account_analytic_account_ids =  [(4, res.id)]
        res.update({
            'user_ids': self.env.user.ids,
        })
        return res
# def action_set_analytic_account(self):
#     user_test = self.env['res.users'].search([])
#     for user in user_test:
#         user._compute_account_analytic_account()

# @api.onchange('name')
# def _onchange_gs_name(self):
#     user = self.env['res.users'].search([('id', '=', self._uid)])
#     if not self.env.user.has_group('base.group_system'):
#         return {'domain': {'group_id': [('id', 'in', user.account_analytic_group_ids.ids)]}}
# @api.model
# def name_search(self, name='', args=None, operator='ilike', limit=100):
#     args = args or []
#
#     # Get the current user
#
#     user = self.env.user
#
#     # Restrict to analytic accounts the user owns
#     allowed_ids = user.account_analytic_account_ids.ids
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
#     return super(GsAccountAnalyticAccountInherit, self).name_search(
#         name=name,
#         args=args,
#         operator=operator,
#         limit=limit,
#     )
