from odoo import fields, models

class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    # Add geofence view type for custom geofence drawing interface
    type = fields.Selection(selection_add=[
        ('geofence_view', 'Geofence View')
    ])
