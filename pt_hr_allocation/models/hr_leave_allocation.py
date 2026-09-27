from odoo import models,fields,api,_
from odoo.exceptions import ValidationError


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    @api.onchange('employee_id')
    def _onchange_employee(self):
        if self.employee_id:
            contract = self.env['hr.contract'].search([('employee_id','=', self.employee_id.id),('state','=', 'open')])
            if contract:
               self.date_to = contract.date_end
            # else:
            #     raise ValidationError(_('Employee Not have Contract'))

    def create(self,vals):
        res = super().create(vals)
        contract = self.env['hr.contract'].search([('employee_id', '=', res.employee_id.id), ('state', '=', 'open')])
        if not contract:
            raise ValidationError(_('Employee Not have Contract'))
        return res

