# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_salesperson_readonly = fields.Boolean(compute="_get_default_salesperson_readonly")

    @api.depends('state', 'partner_id')
    def _get_default_salesperson_readonly(self):
        for rec in self:
            rec.is_salesperson_readonly = False
            if self.env.user.has_group('gs_sales_salesperson_readonly.group_salesperson_readonly') and rec.state != 'draft':
                rec.is_salesperson_readonly = True
