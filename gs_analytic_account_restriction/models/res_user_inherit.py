# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError


class GsResUsersInherit(models.Model):
    _inherit = 'res.users'

    # account_analytic_group_ids = fields.Many2many("account.analytic.group", "account_aa01", "account_aa001", "account_aa0001", string="Analytic Account Groups")
    account_analytic_account_ids = fields.Many2many("account.analytic.account", "account_ana01", "account_ana001", "account_ana0001", string="Analytic Accounts")
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

    # def action_set_analytic_account(self):
    #     user_test = self.env['res.users'].search([])
    #     for user in user_test:
    #         user._compute_account_analytic_account()

    # @api.onchange('name')
    # def _onchange_gs_name(self):
    #     user = self.env['res.users'].search([('id', '=', self._uid)])
    #     if not self.env.user.has_group('base.group_system'):
    #         return {'domain': {'group_id': [('id', 'in', user.account_analytic_group_ids.ids)]}}
    @api.model
    def _search(self, args, offset=0, limit=None, order=None):
        if self.env.user.account_analytic_account_ids.ids:
            args.append(('id', 'in', self.env.user.account_analytic_account_ids.ids))
        res = super(GsAccountAnalyticAccountInherit, self)._search(args, offset=offset, limit=limit,
                                                    order=order)
        return res