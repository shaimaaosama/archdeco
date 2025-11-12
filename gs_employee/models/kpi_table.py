# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GsKPITable(models.Model):
    _name = 'gs.kpi.table'
    _description = 'KPI Table'
    _rec_name = 'task_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    task_id = fields.Many2one('gs.task', string="Tasks", )
    job_id = fields.Many2one('hr.job', string="Job Position",)
    point = fields.Integer(string='Point')
    percentage = fields.Integer(string='Percentage %')
    notes = fields.Text(string="Notes",)
    evaluated_by_ids = fields.Many2many('gs.evaluated.by', string="Evaluated By",)

    @api.model
    def create(self, vals):
        res = super(GsKPITable, self).create(vals)
        res.get_percentage()
        return res

    def get_percentage(self):
        for rec in self:
            kpis = self.env['gs.kpi.table'].search([('job_id', '=', rec.job_id.id)])
            total_point = 0
            for k in kpis:
                total_point += k.point

            for kp in kpis:
                per = (kp.point / total_point) * 100
                kp.percentage = per