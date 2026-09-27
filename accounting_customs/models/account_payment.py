from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    approval_id = fields.Many2one('approval.request')