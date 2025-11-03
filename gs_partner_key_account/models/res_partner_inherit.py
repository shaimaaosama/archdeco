# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError


class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    key_account_ids = fields.Many2many("res.partner", "key_account_ids_gpt01", "key_account_ids_gpt001", "key_account_ids_gpt0001", string="Key Account")


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    key_account_id = fields.Many2one('res.partner', string='Key Account', store=True)
    option_id = fields.Many2one('gs.option', string='Option')
    has_key_account = fields.Boolean(string="Has Key Account?")


class AccountMoveLineInheritKey(models.Model):
    _inherit = 'account.move.line'

    key_account_id = fields.Many2one('res.partner', string='Key Account', store=True, related='partner_id.key_account_id')
    option_id = fields.Many2one('gs.option', string='Option', related='partner_id.option_id')