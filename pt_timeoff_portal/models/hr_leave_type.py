from odoo import fields, models, api

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    hide_leave_counts = fields.Boolean(
        string="Hide Remaining/Max Leaves in Name",
        default=False,
    )

    @api.depends('requires_allocation', 'virtual_remaining_leaves', 'max_leaves', 'request_unit', 'hide_leave_counts')
    @api.depends_context('holiday_status_display_name', 'employee_id')
    def _compute_display_name(self):
        res = super(HrLeaveType,self)._compute_display_name()
        for record in self:
            if record.hide_leave_counts:
                record.display_name = record.name
        return res