from odoo import models,fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        domain="[('customer', '=', True)]",
        ondelete='restrict',
        required=True,
        check_company=True,
    )
