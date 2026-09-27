# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    journal_id = fields.Many2one('account.journal', string='EOS Journal', copy=False)
    account_id = fields.Many2one('account.account', string='EOS Debit Account', copy=False)
    account_credit_id = fields.Many2one('account.account', string='EOS Credit Account', copy=False)

    day_of_operation = fields.Integer(string="Day", copy=False)

    def set_values(self):
        res = super(ResConfigSettingsInherit, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("gs_hr_eos.journal_id", self.journal_id.id)
        self.env['ir.config_parameter'].sudo().set_param("gs_hr_eos.account_id", self.account_id.id)
        self.env['ir.config_parameter'].sudo().set_param("gs_hr_eos.account_credit_id", self.account_credit_id.id)
        self.env['ir.config_parameter'].sudo().set_param("gs_hr_eos.day_of_operation", self.day_of_operation)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsInherit, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        journal_id = params.get_param('gs_hr_eos.journal_id')
        account_id = params.get_param('gs_hr_eos.account_id')
        account_credit_id = params.get_param('gs_hr_eos.account_credit_id')
        day_of_operation = params.get_param('gs_hr_eos.day_of_operation')
        res.update(
            journal_id=journal_id,
            account_id=account_id,
            account_credit_id=account_credit_id,
            day_of_operation= day_of_operation,
        )
        return res

