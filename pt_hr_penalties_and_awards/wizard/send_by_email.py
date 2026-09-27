# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GsSendByEmailWizard(models.TransientModel):
    _name = "gs.send.email.wizard"
    _description = "Penalties And Awards Email Wizard"

    employee_ids = fields.Many2many('hr.employee', 'gs_p_a_employee_ids_01', 'gs_p_a_employee_ids_001', 'gs_p_a_employee_ids_0001', string='Alternative Employee')

    @api.model
    def default_get(self, fields):
        rec = super(GsSendByEmailWizard, self).default_get(fields)
        record = self.env['gs.penalties.awards'].browse(self._context.get('active_ids', []))
        if record and len(record) == 1:
            rec['employee_ids'] = [(4, record.employee_id.id)]
        return rec

    def action_send_email(self):
        active_id = self.env.context.get('active_id')
        penalties_awards = self.env['gs.penalties.awards'].search([('id', '=', active_id)])
        for user in self.employee_ids:
            template = self.env.ref('gs_hr_penalties_and_awards.gs_send_email_template').id
            penalties_awards.send_template_email(user, template)
            penalties_awards.is_send_by_email = True

