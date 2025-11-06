from odoo import models,fields

class Partners(models.Model):
    _inherit = 'res.partner'

    customer = fields.Boolean('Is Customer', default=False)
    vendor = fields.Boolean('Is Vendor', default=False)