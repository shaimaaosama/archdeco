from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_reconcile_method = fields.Selection([
        ('fifo', 'First In First'),
        ('same', 'Same Amount'),
        ('latest', 'Latest Invoice')
    ], string="Auto Reconcile Method",
       config_parameter='auto_reconcile_config.method')
