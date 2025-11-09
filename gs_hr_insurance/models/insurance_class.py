# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GsInsuranceClass(models.Model):
    _name = 'gs.insurance.class'

    name = fields.Char(string='Name', )
    insurance_network_ids = fields.Many2many('gs.insurance.network', string="Insurance Network")
    insurance_count = fields.Integer(compute='get_gs_insurance_count')

    def open_gs_insurance(self):
        return {
            'name': _('Insurance'),
            'domain': [('insurance_class_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'gs.insurance',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_gs_insurance_count(self):
        count = self.env['gs.insurance'].search_count([('insurance_class_id', '=', self.id)])
        self.insurance_count = count
