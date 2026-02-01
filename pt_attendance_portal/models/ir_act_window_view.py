from odoo import fields, models

class IrActionsActWindowView(models.Model):
    _inherit = 'ir.actions.act_window.view'

    # Add geofence view mode for action windows
    view_mode = fields.Selection(
        selection_add=[('geofence_view', 'Geofence View')],
        ondelete={'geofence_view': 'cascade'},
    )
