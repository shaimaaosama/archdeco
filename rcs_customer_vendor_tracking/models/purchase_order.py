from odoo import models,fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    partner_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        domain="[('vendor', '=', True)]",
        ondelete='restrict',
        required=True,
        check_company=True,
    )
