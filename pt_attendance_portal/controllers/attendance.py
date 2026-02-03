from odoo import http, _
from odoo.http import request
import datetime
import logging
from odoo.addons.hr_attendance.controllers.main import HrAttendance as HrAttendance

_logger = logging.getLogger(__name__)

class HrAttendance(HrAttendance):
    """Extended attendance controller with geolocation, geofence, and photo features"""

    @staticmethod
    def _get_employee_info_response(employee):
        """Extend employee info response to include attendance ID"""
        rslt = super(HrAttendance, HrAttendance)._get_employee_info_response(employee)
        rslt['attendance']['id'] = employee.last_attendance_id.id or False
        return rslt
    
    @http.route('/hr_attendance/update_checkin_controls', type="json", auth="public")
    def update_checkin_controls(self, token, attendance_id, check_in_latitude, check_in_longitude, check_in_geofence_ids, check_in_photo, check_in_ipaddress):
        """Update check-in attendance record with geolocation, geofence, photo, and IP data"""
        company = self._get_company(token)
        if company:
            attendance = request.env['hr.attendance'].sudo().browse(attendance_id)
            if attendance:
                attendance.sudo().write({
                    'check_in_latitude': check_in_latitude,
                    'check_in_longitude': check_in_longitude,
                    'check_in_geofence_ids': check_in_geofence_ids,
                    'check_in_photo': check_in_photo,
                    'check_in_ipaddress': check_in_ipaddress,
                })
        return {}
    
    @http.route('/hr_attendance/update_checkout_controls', type="json", auth="public")
    def update_checkout_controls(self, token, attendance_id, check_out_latitude, check_out_longitude, check_out_geofence_ids, check_out_photo, check_out_ipaddress):
        """Update check-out attendance record with geolocation, geofence, photo, and IP data"""
        company = self._get_company(token)
        if company:
            attendance = request.env['hr.attendance'].sudo().browse(attendance_id)
            if attendance:
                attendance.sudo().write({
                    'check_out_latitude': check_out_latitude,
                    'check_out_longitude': check_out_longitude,
                    'check_out_geofence_ids': check_out_geofence_ids,
                    'check_out_photo': check_out_photo,
                    'check_out_ipaddress': check_out_ipaddress,
                })
        return {}
    
    @http.route('/hr_attendance/attendance_res_config', type="json", auth="public",)
    def attendance_res_config(self, token):
        """Get company attendance configuration settings for kiosk mode"""
        company = self._get_company(token)
        conf = {}
        if company:
            conf['hr_attendance_geolocation_k'] = company.hr_attendance_geolocation_k
            conf['hr_attendance_geofence_k'] = company.hr_attendance_geofence_k
            conf['hr_attendance_face_recognition_k'] = company.hr_attendance_face_recognition_k
            conf['hr_attendance_ip_k'] = company.hr_attendance_ip_k
        return conf
    
    @http.route('/hr_attendance/get_geofences/', type="json", auth="public")
    def get_geofences(self, employee_id, token):
        """Get available geofences for a specific employee"""
        if not employee_id:
            return []
        company = self._get_company(token)
        geofences = request.env['hr.attendance.geofence'].sudo().search_read([
            ('company_id', '=', int(company.id)),
            ('employee_ids', 'in',int(employee_id))
            ], ['id', 'name', 'overlay_paths'])
        return geofences

    @http.route('/pt_attendance_portal/device/check', type='json', auth='public')
    def check_device_access(self, employee_id=None, device_mac=None, device_name=None, device_type=None, **kwargs):
        """Check if the device is allowed for the employee"""
        if not employee_id or not device_mac:
            return {'success': False, 'message': 'Missing required parameters'}

        try:
            employee = request.env['hr.employee'].sudo().browse(int(employee_id))
            if not employee.exists():
                return {'success': False, 'message': 'Employee not found'}

            # Check if device check is enabled for the employee
            if not employee.device_check_enabled:
                return {'success': True, 'message': 'Device check disabled for this employee'}

            # Check device access
            allowed_device_model = request.env['hr.employee.allowed.device'].sudo()
            is_allowed, device = allowed_device_model.check_device_access(int(employee_id), device_mac)

            if is_allowed:
                return {'success': True, 'message': 'Device is authorized'}
            else:
                # Check if auto-add is enabled
                if employee.allow_next_device:
                    try:
                        new_device = allowed_device_model.add_device_from_attendance(
                            int(employee_id), device_mac, device_name, device_type
                        )
                        # Disable the auto-add flag after using it
                        employee.write({'allow_next_device': False})
                        return {
                            'success': True, 
                            'message': f'Device automatically added: {new_device.name}',
                            'auto_added': True
                        }
                    except Exception as e:
                        return {'success': False, 'message': f'Failed to auto-add device: {str(e)}'}

                return {'success': False, 'message': 'Device not authorized and auto-add disabled'}

        except Exception as e:
            return {'success': False, 'message': f'Error checking device access: {str(e)}'}

    @http.route('/pt_attendance_portal/device/request_approval', type='json', auth='public')
    def request_device_approval(self, employee_id=None, device_mac=None, device_name=None, **kwargs):
        """Request device approval from administrator"""
        if not employee_id or not device_mac:
            return {'success': False, 'message': 'Missing required parameters'}

        try:
            employee = request.env['hr.employee'].sudo().browse(int(employee_id))
            if not employee.exists():
                return {'success': False, 'message': 'Employee not found'}

            # Create a notification or log the request
            # This could be extended to send emails or create tasks for administrators
            _logger.info(f"Device approval requested for employee {employee.name} (ID: {employee_id}) - Device: {device_name} (MAC: {device_mac})")
            
            return {
                'success': True, 
                'message': 'Device approval request submitted. Please contact your administrator.'
            }

        except Exception as e:
            return {'success': False, 'message': f'Error requesting device approval: {str(e)}'}

    @http.route('/pt_attendance_portal/cooldown/check', type='json', auth='public')
    def check_cooldown_period(self, employee_id=None, **kwargs):
        """Check if employee can make another attendance entry (3-minute cooldown)"""
        if not employee_id:
            return {'success': False, 'message': 'Missing employee ID'}

        try:
            attendance_model = request.env['hr.attendance'].sudo()
            can_proceed, message = attendance_model.check_cooldown_period(int(employee_id))
            
            return {
                'success': can_proceed,
                'message': message,
                'cooldown_violation': not can_proceed
            }

        except Exception as e:
            _logger.error(f"Error checking cooldown period: {e}")
            return {'success': False, 'message': f'Error checking cooldown: {str(e)}'}