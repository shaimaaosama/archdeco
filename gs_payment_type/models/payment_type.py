# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class GSAccountPaymentType(models.Model):
    _name = 'gs.account.payment.type'

    name = fields.Char(string='Name')
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], default='customer', tracking=True, required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    destination_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Destination Account',
        store=True, readonly=False,
        compute='_compute_destination_account_id',
        check_company=True)