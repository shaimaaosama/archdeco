# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    attendance_latitude = fields.Float(
        related='company_id.attendance_latitude', readonly=False,
        string='Attendance Latitude')
    attendance_longitude = fields.Float(
        related='company_id.attendance_longitude', readonly=False,
        string='Attendance Longitude')
    attendance_radius = fields.Float(
        related='company_id.attendance_radius', readonly=False,
        string='Attendance Radius (m)')
    mobile_late_grace_minutes = fields.Integer(
        related='company_id.mobile_late_grace_minutes', readonly=False,
        string='Late Grace Period (minutes)')
    mobile_block_mock_location = fields.Boolean(
        related='company_id.mobile_block_mock_location', readonly=False,
        string='Block Mock Locations')
