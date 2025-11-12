

from odoo import api, fields, Command, models, _
from odoo.exceptions import UserError
from odoo.tools import email_split, float_is_zero, float_repr, float_compare, is_html_empty
from odoo.tools.misc import clean_context, format_date


class HRLeaveInherit(models.Model):
    _inherit = 'hr.leave'

    number_of_days_display = fields.Float(
        'Duration in days', compute='_compute_number_of_days_display_new', readonly=True,
        help='Number of days of the time off request according to your working schedule. Used for interface.')

    number_of_days = fields.Float(
        'Duration (Days)', compute='_compute_number_of_days_display_new', store=True, readonly=False, copy=False, tracking=True,
        help='Number of days of the time off request. Used in the calculation. To manually correct the duration, use this field.')

    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_number_of_days_display_new(self):
        for rec in self:
            wd_diff = fields.Datetime.from_string(rec.date_to) - fields.Datetime.from_string(rec.date_from)
            rec.number_of_days_display = wd_diff.days
            rec.number_of_days_display += 1
            rec.number_of_days = rec.number_of_days_display