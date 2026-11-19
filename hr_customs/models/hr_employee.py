from odoo import models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _get_special_calendar(self, day, regular_calendar=None, special_calendars=None):
        """The working schedule applied to the employee on ``day``: the most specific matching special working schedule, ``regular_calendar`` (the employee's schedule by default) otherwise."""
        self.ensure_one()
        if regular_calendar is None:
            regular_calendar = self.resource_calendar_id
        if special_calendars is None:
            special_calendars = self.env['resource.calendar']._get_special_calendars(day, day)
        choices = []
        nationality = self.country_id.id
        religion = self.religion if 'religion' in self._fields else False
        for calendar in special_calendars:
            if not calendar.special_date_from or not calendar.special_date_to or not calendar.special_date_from <= day <= calendar.special_date_to:
                continue
            if calendar.special_company_ids and self.company_id not in calendar.special_company_ids:
                continue
            if calendar.special_department_ids and self.department_id not in calendar.special_department_ids:
                continue
            if calendar.special_employee_ids and self not in calendar.special_employee_ids:
                continue
            if calendar.special_nationality_ids and nationality not in calendar.special_nationality_ids.ids:
                continue
            if calendar.special_religion and religion != calendar.special_religion:
                continue
            rank = (bool(calendar.special_employee_ids), bool(calendar.special_department_ids), bool(calendar.special_company_ids), int(bool(calendar.special_nationality_ids)) + int(bool(calendar.special_religion)), calendar.special_date_from, calendar.id)
            choices.append((rank, calendar))
        return max(choices, key=lambda item: item[0])[1] if choices else regular_calendar
