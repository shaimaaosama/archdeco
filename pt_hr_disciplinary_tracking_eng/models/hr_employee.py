from odoo import models, fields
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def calculate_disciplinary_action(self, amount, date_from, date_to):
        disciplinary_action_objs = self.env['disciplinary.action'].search(
            [('state', '=', 'action'), ('applied_date', '>=', date_from), ('applied_date', '<=', date_to),
             ('employee_name', '=', self.id)])
        amount_per_hour = 0.0
        for disciplinary_action_obj in disciplinary_action_objs:
            if disciplinary_action_obj.role_by == 'fixed':
                amount_per_hour += disciplinary_action_obj.amount
            elif disciplinary_action_obj.role_by == 'percentage':
                if disciplinary_action_obj.by_percentage_type == 'wage':
                    amount_per_hour += self.contract_id.wage * disciplinary_action_obj.percentage / 100
                elif disciplinary_action_obj.by_percentage_type == 'gross':
                    amount_per_hour += self.contract_id.gross * disciplinary_action_obj.percentage / 100
                elif disciplinary_action_obj.by_percentage_type == 'net':
                    amount_per_hour += self.contract_id.net * disciplinary_action_obj.percentage / 100
            elif disciplinary_action_obj.role_by == 'time':
                amount_per_hour += disciplinary_action_obj.amount * amount
            elif disciplinary_action_obj.role_by == 'days':
                amount_per_hour += amount * disciplinary_action_obj.amount
        return amount_per_hour
