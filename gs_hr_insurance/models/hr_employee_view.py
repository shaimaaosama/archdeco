# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GsHrEmployeeFamily(models.Model):
    _inherit = 'hr.employee.family'

    follower_id = fields.Many2one('gs.follower', string='Name')
    relation_id = fields.Many2one('hr.employee.relation', string="Relation", help="Relationship with the employee", related="follower_id.relation_id")
    birth_date = fields.Date(string="DOB", tracking=True, related="follower_id.date_of_birth")
    gender = fields.Selection(string='Gender', selection=[('male', 'Male'), ('female', 'Female'), ], related="follower_id.gender")


class GsFollower(models.Model):
    _inherit = 'hr.employee'

    follower_id = fields.Many2one('gs.follower', string='Name')

    follower_count = fields.Integer(compute='_follower_count', string='#follower')

    def _follower_count(self):
        for each in self:
            followers = self.env['gs.follower'].search([('employee_id', '=', each.id)])
            each.follower_count = len(followers)

    def follower_view(self):
        for each1 in self:
            followers = self.env['gs.follower'].search([('employee_id', '=', each1.id)])
            follower_ids = []
            for follower in followers:
                follower_ids.append(follower.id)
            view_id = self.env.ref('gs_hr_insurance.gs_follower_view_form').id
            if follower_ids:
                if len(follower_ids) <= 1:
                    value = {
                        'view_mode': 'form',
                        'res_model': 'gs.follower',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Follower'),
                        'res_id': follower_ids and follower_ids[0],
                        'context': {'default_employee_id': each1.id},

                    }
                else:
                    value = {
                        'domain': [('id', 'in', follower_ids)],
                        'view_mode': 'tree,form',
                        'res_model': 'gs.follower',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name': _('Follower'),
                        'context': {'default_employee_id': each1.id},

                    }

                return value

            else:
                return {
                    'name': _('Follower'),
                    'view_mode': 'tree,form',
                    'res_model': 'gs.follower',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'domain': [('employee_id', '=', each1.id)],
                    'context': {'default_employee_id': each1.id},
                }
