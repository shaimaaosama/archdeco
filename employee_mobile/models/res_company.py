# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    attendance_latitude = fields.Float(
        string='Attendance Latitude', digits=(10, 7),
        help="Latitude used for the mobile app geofence when an employee's attendance "
             "restriction is set to Company.")
    attendance_longitude = fields.Float(
        string='Attendance Longitude', digits=(10, 7),
        help="Longitude used for the mobile app geofence when an employee's attendance "
             "restriction is set to Company.")
    attendance_radius = fields.Float(string='Attendance Radius (m)', default=100.0)
    mobile_late_grace_minutes = fields.Integer(
        string='Late Grace Period (minutes)', default=0,
        help="Number of minutes after the scheduled start time before a check-in from "
             "the mobile app is considered late.")
    mobile_block_mock_location = fields.Boolean(
        string='Block Mock Locations', default=True,
        help="Reject mobile app check-in/check-out when the device reports a mocked "
             "(fake) GPS location.")
