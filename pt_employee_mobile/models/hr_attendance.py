# -*- coding: utf-8 -*-
from odoo import fields, models


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    # Shared with pt_attendance_portal: same field names, type and strings, so both
    # modules can be installed together (and either one can be uninstalled without
    # losing the underlying "hr_attendance" numeric columns / data). Kept at
    # digits=(10, 7) here on purpose: never depend on the portal's "Gelocation"
    # decimal precision record, since that is deleted when the portal is uninstalled.
    check_in_latitude = fields.Float("Check-in Latitude", digits=(10, 7), readonly=True)
    check_in_longitude = fields.Float("Check-in Longitude", digits=(10, 7), readonly=True)
    check_out_latitude = fields.Float("Check-out Latitude", digits=(10, 7), readonly=True)
    check_out_longitude = fields.Float("Check-out Longitude", digits=(10, 7), readonly=True)

    mobile_check_in_location = fields.Char(
        string='Mobile Check-in Location', help="Name of the work location/company "
        "the mobile app matched this check-in against.")
    mobile_check_out_location = fields.Char(string='Mobile Check-out Location')
    mobile_check_in_distance = fields.Float(
        string='Mobile Check-in Distance (m)',
        help="Distance in metres between the employee and the geofence centre at check-in.")
    mobile_check_out_distance = fields.Float(string='Mobile Check-out Distance (m)')

    in_mode = fields.Selection(selection_add=[('mobile', 'Mobile App')],
                                ondelete={'mobile': 'set default'})
    out_mode = fields.Selection(selection_add=[('mobile', 'Mobile App')],
                                 ondelete={'mobile': 'set default'})
