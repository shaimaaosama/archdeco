# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError


class GsDirectlyWork(models.Model):
    _name = 'gs.directly.work'
    _description = 'Directly Work'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee')
    type = fields.Selection(string='Type',
                            selection=[('re_lev', 'Return of leave'),
                                       ('n_appo', 'New appointment'),
                                       ('end_service', 'End Of Service'),
                                       ],
                            required=True, )

    date = fields.Date(string='Date')
    leave_id = fields.Many2one('hr.leave', domain="[('employee_id', '=', employee_id)]")

    leave_id = fields.Many2one('hr.leave', domain="[('employee_id', '=', employee_id)]")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='Status', default='draft')

    # @api.onchange('leave_id')
    def update_work_entry(self):
        print('update_work_entry')
        for rec in self:
            if rec.leave_id:
                leave_start = rec.leave_id.date_from
                leave_end = rec.leave_id.date_to

                work_entries = self.env['hr.work.entry'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    '|',
                    '&', ('date_start', '>=', leave_start), ('date_start', '<=', leave_end),
                    '&', ('date_stop', '>=', leave_start), ('date_stop', '<=', leave_end)
                ])

                for work in work_entries:
                    if rec.date <= work.date_start.date():
                        work.work_entry_type_id = self.env.ref('hr_work_entry.work_entry_type_attendance')


    def action_confirm(self):
        for rec in self:
            if rec.type == 're_lev' and rec.leave_id:
                leave_start = rec.leave_id.date_from.date()
                leave_end = rec.leave_id.date_to.date()
                if rec.date < leave_start or rec.date > leave_end:
                    raise ValidationError(
                        "The return date must be within the leave period between {} and {}".format(
                            leave_start, leave_end
                        )
                    )
                else:
                    rec.update_work_entry()
                    rec.state = 'done'
            else:
                rec.state = 'done'
