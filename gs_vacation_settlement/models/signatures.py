# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GsSignatures(models.Model):
    _name = 'gs.signatures.settlement'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    company_id = fields.Many2one('res.company', string='Company')
    type = fields.Selection(
        string='Type',
        selection=[
            ('gro', 'Government Relation Officer'),
            ('hos', 'HR Operations Supervisor'),
            ('pcc', 'Payment Clerk - Cashier'),
            ('am', 'Account Manager'),
            ('hrm', 'Human Resources Manager'),
            ('fm', 'Finance Manager'),
            ('ceo', 'CEO'),
        ],
        required=True, )

