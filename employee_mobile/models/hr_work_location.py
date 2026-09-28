# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrWorkLocation(models.Model):
    _inherit = 'hr.work.location'

    attendance_latitude = fields.Float(
        string='Attendance Latitude', digits=(10, 7),
        help="Latitude of this work location's site centre, used for the mobile app geofence.")
    attendance_longitude = fields.Float(
        string='Attendance Longitude', digits=(10, 7),
        help="Longitude of this work location's site centre, used for the mobile app geofence.")
    attendance_radius = fields.Float(
        string='Attendance Radius (m)', default=100.0,
        help="Employees must be within this many metres of the site centre to "
             "check in/out from the mobile app.")
    attendance_map_url = fields.Char(string='Map', compute='_compute_attendance_map_url')

    @api.depends('attendance_latitude', 'attendance_longitude')
    def _compute_attendance_map_url(self):
        for location in self:
            if location.attendance_latitude or location.attendance_longitude:
                location.attendance_map_url = 'https://maps.google.com/maps?q=%s,%s' % (
                    location.attendance_latitude, location.attendance_longitude)
            else:
                location.attendance_map_url = False
