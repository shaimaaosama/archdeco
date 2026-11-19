from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    is_special_schedule = fields.Boolean(string='Special Working Schedule', copy=False)
    special_date_from = fields.Date(string='Start Date', copy=False)
    special_date_to = fields.Date(string='End Date', copy=False)
    special_company_ids = fields.Many2many('res.company', 'resource_calendar_special_company_rel', 'calendar_id', 'company_id', string='Companies', copy=False)
    special_department_ids = fields.Many2many('hr.department', 'resource_calendar_special_department_rel', 'calendar_id', 'department_id', string='Departments', copy=False)
    special_employee_ids = fields.Many2many('hr.employee', 'resource_calendar_special_employee_rel', 'calendar_id', 'employee_id', string='Employees', copy=False)
    special_nationality_ids = fields.Many2many('res.country', 'resource_calendar_special_nationality_rel', 'calendar_id', 'country_id', string='Nationalities', copy=False)
    special_religion = fields.Selection([('mus', 'Muslim'), ('non_mus', 'Non-Muslim')], string='Religion', copy=False)

    @api.constrains('is_special_schedule', 'special_date_from', 'special_date_to')
    def _check_special_schedule_dates(self):
        for rec in self:
            if rec.is_special_schedule:
                if not rec.special_date_from or not rec.special_date_to:
                    raise ValidationError(_('Start Date and End Date are required for a special working schedule.'))
                if rec.special_date_from > rec.special_date_to:
                    raise ValidationError(_('The Start Date cannot be later than the End Date.'))

    @api.model
    def _get_special_calendars(self, date_from, date_to):
        """Active special working schedules overlapping [date_from, date_to]."""
        return self.search([('active', '=', True), ('is_special_schedule', '=', True), ('special_date_from', '<=', date_to), ('special_date_to', '>=', date_from)], order='special_date_from desc, id desc')
