# -*- coding: utf-8 -*-

from odoo import models, fields


class GsPenaltiesAwardsSetting(models.Model):
    _name = 'gs.penalties.awards.setting'
    _description = 'Penalties & Awards Setting'

    name = fields.Char()
    type = fields.Selection(string='Type', selection=[('deduction', 'Deduction'), ('award', 'Award'),
                                                      ],)

    is_type_fixed = fields.Boolean(string='Is Fixed Amount?', required=False)

    base_amount_ids = fields.Many2many('allowances.collect', 'base_amount_ids01', 'base_amount_ids001',
                                       'base_amount_ids0001')

    base_num = fields.Integer(string='Base Number',)
    penalty_labour = fields.Boolean('مخالفه وزاره العمل')
    country_labour = fields.Boolean('مخالفه البلدية')
    penalty_employee = fields.Boolean('مخالفه الموظف')

    # ///////////////////////////////////////////////////////////
    # 🔹 New fields
    account_debit_id = fields.Many2one(
        'account.account',
        string='Debit Account',
        domain=[('deprecated', '=', False)],
        help="Select the debit account for this penalty/award."
    )
    account_credit_id = fields.Many2one(
        'account.account',
        string='Credit Account',
        domain=[('deprecated', '=', False)],
        help="Select the credit account for this penalty/award."
    )