from odoo import fields, models, api

class ResCompany(models.Model):
    _inherit = "res.company"
    
    # Attendance feature flags for general use
    hr_attendance_geolocation = fields.Boolean(string="Geolocation", default=False)
    hr_attendance_geofence = fields.Boolean(string="Geofence", default=False)
    hr_attendance_face_recognition = fields.Boolean(string="Photo", default=False)
    hr_attendance_photo = fields.Boolean(string="Photo", default=False)
    hr_attendance_ip = fields.Boolean(string="IP Address", default=False)
    hr_attendance_reason = fields.Boolean(string="Reason", default=False)
    
    # Attendance feature flags for kiosk mode
    hr_attendance_geolocation_k = fields.Boolean(string="Geolocation", default=False)
    hr_attendance_geofence_k = fields.Boolean(string="Geofence", default=False)
    hr_attendance_face_recognition_k = fields.Boolean(string="Photo", default=False)
    hr_attendance_ip_k = fields.Boolean(string="IP Address", default=False)

    # Attendance feature flags for portal mode
    hr_attendance_geolocation_p = fields.Boolean(string="Geolocation", default=False)
    hr_attendance_geofence_p = fields.Boolean(string="Geofence", default=False)
    hr_attendance_face_recognition_p = fields.Boolean(string="Photo", default=False)
    hr_attendance_ip_p = fields.Boolean(string="IP Address", default=False)
    hr_attendance_reason_p = fields.Boolean(string="Reason", default=False)

    # Kiosk attendance mode selection
    attendance_kiosk_mode = fields.Selection([
        ('barcode', 'Barcode / RFID'),
        ('barcode_manual', 'Barcode / Face Recognition / RFID and Manual Selection'),
        ('manual', 'Manual Selection'),
    ], string='Attendance Mode', default='barcode_manual')