import uuid
import werkzeug.urls
import logging
from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

# Precision for geolocation coordinates
GEOLOCATION = dp.get_precision("Gelocation")

class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def _get_default_access_token(self):
        """Generate unique access token for portal access"""
        return str(uuid.uuid4())
    
    # Portal access fields
    access_url = fields.Char('Portal Access URL', compute='_compute_access_url',help='Contract Portal URL')
    access_token = fields.Char('Access Token', default=lambda self: self._get_default_access_token(), copy=False)

    # Geolocation fields for check-in
    check_in_latitude = fields.Float("Check-in Latitude", digits=GEOLOCATION, readonly=True)
    check_in_longitude = fields.Float("Check-in Longitude", digits=GEOLOCATION, readonly=True)
        
    # Geolocation fields for check-out
    check_out_latitude = fields.Float("Check-out Latitude", digits=GEOLOCATION, readonly=True)
    check_out_longitude = fields.Float("Check-out Longitude", digits=GEOLOCATION, readonly=True)
    
    # Google Maps location links
    check_in_location_link = fields.Char('Check In Location', compute='_compute_check_in_location_url')
    check_out_location_link = fields.Char('Check Out Location', compute='_compute_check_out_location_url')
    
    # Geofence relationships
    check_in_geofence_ids = fields.Many2many('hr.attendance.geofence', 'check_in_geofence_attendance_rel', 'attendance_id', 'geofence_id', string='Geofences')
    check_out_geofence_ids = fields.Many2many('hr.attendance.geofence', 'check_out_geofence_attendance_rel', 'attendance_id', 'geofence_id', string='Geofences')
    
    # Photo capture fields
    check_in_photo = fields.Binary(string="Check In Photo", readonly=False)
    check_out_photo = fields.Binary(string="Check Out Photo", readonly=False)
    
    # IP address tracking
    check_in_ipaddress = fields.Char(string="Check In IP", readonly=True)
    check_out_ipaddress = fields.Char(string="Check Out IP", readonly=True)
    
    # Reason fields for check-in/out
    check_in_reason = fields.Char("Check In Reason")
    check_out_reason = fields.Char("Check Out Reason")
    
    @api.depends('check_in_latitude','check_in_longitude')
    def _compute_check_in_location_url(self):
        """Generate Google Maps URL for check-in location"""
        for attendance in self:
            params = {
                'q': '%s,%s' % (attendance.check_in_latitude or '',attendance.check_in_longitude or ''),'z': 10,
            }
            attendance.check_in_location_link ='%s?%s' % ('https://maps.google.com/maps',werkzeug.urls.url_encode(params or None))

    @api.depends('check_out_latitude','check_out_longitude')
    def _compute_check_out_location_url(self):
        """Generate Google Maps URL for check-out location"""
        for attendance in self:
            params = {
                'q': '%s,%s' % (attendance.check_out_latitude or '',attendance.check_out_longitude or ''),'z': 10,
            }
            attendance.check_out_location_link = '%s?%s' % ('https://maps.google.com/maps',werkzeug.urls.url_encode(params or None))

    def _compute_access_url(self):
        """Generate portal access URL for attendance record"""
        for attendance in self:
            attendance.access_url = '/my/hr_attendance/%s' % attendance.id
    
    def _portal_ensure_token(self):
        """Ensure access token exists for portal access"""
        if not self.access_token:
            self.sudo().write({'access_token': str(uuid.uuid4())})
        return self.access_token
    
    def get_portal_url(self, suffix=None, report_type=None, download=None, query_string=None, anchor=None):
        """
        Generate portal URL with access token and optional parameters
        - suffix: string to append to the url, before the query string
        - report_type: report_type query string, often one of: html, pdf, text
        - download: set the download query string to true
        - query_string: additional query string
        - anchor: string to append after the anchor #
        """
        self.ensure_one()
        url = self.access_url + '%s?access_token=%s%s%s%s%s' % (
            suffix if suffix else '',
            self._portal_ensure_token(),
            '&report_type=%s' % report_type if report_type else '',
            '&download=true' if download else '',
            query_string if query_string else '',
            '#%s' % anchor if anchor else ''
        )
        return url

    def _get_portal_return_action(self):
        """Return action for displaying attendance records in portal"""
        self.ensure_one()
        return self.env.ref('hr_attendance.hr_attendance_action')

    def preview_hr_attendance(self):
        """Open attendance record in portal view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

    def check_device_access(self, employee_id, mac_address, device_name=None):
        """Check if the device is allowed for the employee and handle auto-adding if enabled"""
        try:
            allowed_device_model = self.env['hr.employee.allowed.device']
            employee = self.env['hr.employee'].browse(employee_id)
            
            if not employee.exists():
                return False, "Employee not found"
            
            # Check if device check is enabled
            if not employee.device_check_enabled:
                return True, "Device check disabled"
            
            # Check if device is allowed
            is_allowed, device = allowed_device_model.check_device_access(employee_id, mac_address)
            
            if is_allowed:
                return True, "Device allowed"
            
            # If not allowed but auto-add is enabled, add the device
            if employee.allow_next_device:
                try:
                    new_device = allowed_device_model.add_device_from_attendance(
                        employee_id, mac_address, device_name
                    )
                    # Disable the auto-add flag after using it
                    employee.write({'allow_next_device': False})
                    return True, f"Device automatically added: {new_device.name}"
                except Exception as e:
                    _logger.error(f"Failed to auto-add device: {e}")
                    return False, "Failed to auto-add device"
            
            return False, "Device not allowed and auto-add disabled"
            
        except Exception as e:
            _logger.error(f"Error checking device access: {e}")
            return False, f"Error: {str(e)}"

    def create_attendance_with_device_check(self, employee_id, attendance_type='check_in', device_mac=None, device_name=None, **kwargs):
        """Create attendance record with device checking"""
        try:
            # Check device access if MAC address is provided
            if device_mac:
                is_allowed, message = self.check_device_access(employee_id, device_mac, device_name)
                if not is_allowed:
                    return {
                        'success': False,
                        'message': message,
                        'attendance_id': None
                    }
            
            # Create attendance record
            attendance_vals = {
                'employee_id': employee_id,
                **kwargs
            }
            
            attendance = self.create(attendance_vals)
            
            return {
                'success': True,
                'message': 'Attendance created successfully',
                'attendance_id': attendance.id
            }
            
        except Exception as e:
            _logger.error(f"Error creating attendance with device check: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}",
                'attendance_id': None
            }

    def check_cooldown_period(self, employee_id):
        """Check if employee can make another attendance entry (3-minute cooldown)"""
        try:
            # Get the last attendance record for this employee
            last_attendance = self.search([
                ('employee_id', '=', employee_id)
            ], order='check_in desc', limit=1)
            
            if not last_attendance:
                return True, "No previous attendance found"
            
            # Calculate time difference from last attendance action
            now = fields.Datetime.now()
            
            # Use check_out time if available, otherwise use check_in time
            if last_attendance.check_out:
                last_time = last_attendance.check_out
            else:
                last_time = last_attendance.check_in
            
            time_diff = now - last_time
            cooldown_minutes = 3
            
            if time_diff.total_seconds() < (cooldown_minutes * 60):
                remaining_seconds = (cooldown_minutes * 60) - time_diff.total_seconds()
                remaining_minutes = int(remaining_seconds // 60)
                remaining_seconds = int(remaining_seconds % 60)
                
                return False, f"Please wait {remaining_minutes} minutes and {remaining_seconds} seconds before making another attendance entry."
            
            return True, "Cooldown period passed"
            
        except Exception as e:
            _logger.error(f"Error checking cooldown period: {e}")
            return False, f"Error checking cooldown: {str(e)}"