# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError


class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    account_ids = fields.Many2many("account.account", "account_coa01", "account_coa001", "account_coa0001", string="Accounts")
