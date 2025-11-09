# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GsTypeOfContracts(models.Model):
    _name = 'gs.type.of.contracts'
    _description = 'Contract Classification'

    name = fields.Char()
    contract_classification_id = fields.Many2one('gs.type.of.contracts', string='Contract Classification Category',)
    name_contract_classification = fields.Char(string="Name")

    @api.model
    def create(self, vals):
        res = super(GsTypeOfContracts, self).create(vals)
        res._get_name()
        return res

    def _get_name(self):
        for rec in self:
            if rec.contract_classification_id.name:
                rec.name_contract_classification = str(rec.name) + ' / ' + str(rec.contract_classification_id.name)
            else:
                rec.name_contract_classification = str(rec.name)

    def name_get(self):
        res = []
        for rec in self:
            if rec.contract_classification_id.name:
                res.append((rec.id, "%s / %s" % (rec.name, rec.contract_classification_id.name)))
            else:
                res.append((rec.id, "%s" % (rec.name)))
        return res

    classification_count = fields.Integer(compute='get_gs_classification_count')

    def open_gs_classification(self):
        return {
            'name': _('Contract Classification'),
            'domain': [('contract_classification_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'gs.type.of.contracts',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_gs_classification_count(self):
        count = self.env['gs.type.of.contracts'].search_count([('contract_classification_id', '=', self.id)])
        self.classification_count = count