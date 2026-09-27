from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _get_employee_from_user(self, user_id=None):
        """Get employee record from user."""
        if not user_id:
            user_id = self.env.user.id

        employee = self.env['hr.employee'].sudo().search([
            ('user_id', '=', user_id)
        ], limit=1)

        return employee
