# -*- coding: utf-8 -*-

from odoo import models, fields


class GsEndReason(models.Model):
    _name = 'gs.end.reason'
    _description = 'End Reason'

    name = fields.Char(string='Name', translate=True)
    contract_type = fields.Selection(string='Type of Contract', selection=[('fixed_time', 'Fixed time'),
                                                                           ('unlimited_period', 'Unlimited period'), ], required=False, )
