# -*- coding: utf-8 -*-

from odoo import models, fields, _


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    penalties_awards_id = fields.Many2one('gs.penalties.awards', string='Name')

    penalties_awards_count = fields.Integer(compute='_penalties_awards_count', string='#Penalties & Awards')

    def _penalties_awards_count(self):
        for each in self:
            penalties_awards = self.env['gs.penalties.awards'].search([('employee_id', '=', each.id)])
            each.penalties_awards_count = len(penalties_awards)

    def penalties_awards_view(self):
        for each1 in self:
            penalties_awards = self.env['gs.penalties.awards'].search([('employee_id', '=', each1.id)])
            penalties_awards_ids = []
            for penalties_award in penalties_awards:
                penalties_awards_ids.append(penalties_award.id)
            view_id = self.env.ref('gs_hr_penalties_and_awards.gs_penalties_awards_view_form').id
            if penalties_awards_ids:
                if len(penalties_awards_ids) <= 1:
                    value = {
                        'view_mode': 'form',
                        'res_model': 'gs.penalties.awards',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Penalties & Awards'),
                        'res_id': penalties_awards_ids and penalties_awards_ids[0],
                        'context': {'default_employee_id': each1.id, 'search_default_group_by_type': 1},

                    }
                else:
                    value = {
                        'domain': [('id', 'in', penalties_awards_ids)],
                        'view_mode': 'tree,form',
                        'res_model': 'gs.penalties.awards',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name': _('Penalties & Awards'),
                        'context': {'default_employee_id': each1.id, 'search_default_group_by_type': 1},

                    }

                return value

            else:
                return {
                    'name': _('Penalties & Awards'),
                    'view_mode': 'tree,form',
                    'res_model': 'gs.penalties.awards',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'domain': [('employee_id', '=', each1.id)],
                    'context': {'default_employee_id': each1.id, 'search_default_group_by_type': 1},
                }
