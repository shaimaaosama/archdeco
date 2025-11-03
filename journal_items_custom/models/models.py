# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.fields import first


class AccountMoveLineInheritCustom(models.Model):
    _inherit = 'account.move.line'


    account_invisible = fields.Boolean(compute='_compute_account_invisible')


    def _compute_account_invisible(self):
        for record in self:
            if self.env.user.has_group('account.group_account_manager'):
                record.account_invisible = False
            else:
                record.account_invisible = True
