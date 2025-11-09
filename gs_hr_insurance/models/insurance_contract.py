# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    company_unique_id = fields.Char(string='Company Unique Id', help="New field in follower and insurance record")


class GsInsuranceContract(models.Model):
    _name = 'gs.insurance.contract'
    _rec_name = 'policy_number'

    name = fields.Char(string='Name', )
    company_id = fields.Many2one('res.company', string='Company',)
    company_unique_id = fields.Char(string='Company Unique Id', related="company_id.company_unique_id")
    active_bol = fields.Boolean(string='Active',)
    attachment = fields.Binary(string="Attachment", )
    policy_number = fields.Char(string='Policy Number')

    partner_id = fields.Many2one('res.partner', string='Partner')
    start_date = fields.Date(string="Start Date",)
    end_date = fields.Date(string="End Date",)
    insurance_network_ids = fields.Many2many('gs.insurance.network', string="Insurance Network")

    insurance_count = fields.Integer(compute='get_gs_insurance_count')

    def open_gs_insurance(self):
        return {
            'name': _('Insurance'),
            'domain': [('policy_number_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'gs.insurance',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_gs_insurance_count(self):
        count = self.env['gs.insurance'].search_count([('policy_number_id', '=', self.id)])
        self.insurance_count = count
