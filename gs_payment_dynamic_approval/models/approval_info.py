from odoo import api, fields, tools, models, _


class ApprovalInfo(models.Model):
    _inherit = 'gs.approval.info'
    _description = "Approval Information"

    payment_order_id = fields.Many2one('gs.payment.order')
