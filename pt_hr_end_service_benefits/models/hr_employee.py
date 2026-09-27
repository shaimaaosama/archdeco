# -*- coding: utf-8 -*-
from odoo import models, fields


class Employee(models.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'

    def _get_end_service_benefits_count(self):
        """compute number of rewords for employee"""
        for record in self:
            counter = self.env['hr.end.service.benefit'].search_count(
                [('employee_id', '=', record.id)])
            record.end_service_benefits_count = counter

    end_service_benefits_count = fields.Integer(string="Rewards Count", compute=_get_end_service_benefits_count)
    hiring_date = fields.Date(string="Hiring Date", related='contract_id.date_hired')
    address_home_id = fields.Many2one(
        'res.partner', 'Private Address',
        help='Enter here the private address of the employee, not the one linked to your company.',
        groups="base.group_user")
