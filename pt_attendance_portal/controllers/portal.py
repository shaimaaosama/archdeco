import json
import datetime

from odoo.http import request
from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from collections import OrderedDict
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from operator import itemgetter
from odoo.osv.expression import OR
from dateutil.relativedelta import relativedelta
from odoo.tools import date_utils, groupby as groupbyelem
from odoo.tools import float_round

class PortalAttendanceFacerecognitionController (http.Controller):
    """Controller for portal attendance with face recognition and geolocation features"""
    
    @staticmethod
    def _get_geoip_portal_response(mode, latitude=False, longitude=False):
        """Get geolocation data from request or provided coordinates"""
        return {
            'city': request.geoip.city.name or _('Unknown'),
            'country_name': request.geoip.country.name or request.geoip.continent.name or _('Unknown'),
            'latitude': latitude or request.geoip.location.latitude or False,
            'longitude': longitude or request.geoip.location.longitude or False,
            'ip_address': request.geoip.ip,
            'browser': request.httprequest.user_agent.browser,
            'mode': mode
        }
    
    @staticmethod
    def _get_portal_user_attendance_data(employee):
        """Get employee attendance data for portal display"""
        response = {}
        if employee:
            response = {
                'id': employee.id,
                'hours_today': float_round(employee.hours_today, precision_digits=2),
                'hours_previously_today': float_round(employee.hours_previously_today, precision_digits=2),
                'last_attendance_worked_hours': float_round(employee.last_attendance_worked_hours, precision_digits=2),
                'last_check_in': employee.last_check_in,
                'attendance_state': employee.attendance_state,
                'display_systray': employee.company_id.attendance_from_systray,
            }
        return response
    
    @staticmethod
    def _get_employee_portal_info(employee):
        """Get comprehensive employee information for portal display"""
        response = {}
        if employee:
            response = {
                **PortalAttendanceFacerecognitionController._get_portal_user_attendance_data(employee),
                'employee_name': employee.name,
                'employee_avatar': employee.image_256,
                'total_overtime': float_round(employee.total_overtime, precision_digits=2),
                'kiosk_delay': employee.company_id.attendance_kiosk_delay * 1000,
                'attendance': {
                    'check_in': employee.last_attendance_id.check_in,
                    'check_out': employee.last_attendance_id.check_out,
                    'id': employee.last_attendance_id.id or False,
                },
                'overtime_today': request.env['hr.attendance.overtime'].sudo().search([
                    ('employee_id', '=', employee.id), ('date', '=', datetime.date.today()),
                    ('adjustment', '=', False)]).duration or 0,
                'use_pin': employee.company_id.attendance_kiosk_use_pin,
                'display_overtime': employee.company_id.hr_attendance_display_overtime
            }
        return response
    
    @http.route('/pt_attendance_portal/search_read/get_employee_data', type='json', auth='user', website=True)
    def get_employee_data(self, employee_id, **post):
        """Get employee data by ID for portal operations"""
        if employee_id:
            hr_employee =  request.env['hr.employee'].sudo().search_read([('id', '=', int(employee_id))])
            return hr_employee
        else:
            return False
    
    @http.route('/pt_attendance_portal/check_employee_face_descriptors', type='json', auth='user', website=True)
    def check_employee_face_descriptors(self, employee_id, **post):
        """Check if an employee has face descriptors for face recognition validation"""
        if employee_id:
            employee = request.env['hr.employee'].sudo().browse(int(employee_id))
            if employee.exists():
                # Check if employee has face recognition enabled and any face descriptors
                has_descriptors = employee.face_recognition_enabled and any(face.descriptor and face.descriptor != 'false' for face in employee.user_faces)
                return {
                    'employee_id': employee.id,
                    'has_face_descriptors': has_descriptors,
                    'face_count': len(employee.user_faces)
                }
        return {'has_face_descriptors': False, 'face_count': 0}
        
    @http.route('/hr_attendance/portal_manual_selection', type="json", auth="public")
    def portal_manual_selection(self, employee_id):
        """Handle manual employee selection for attendance in portal"""
        company = request.env.company
        if company:
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            if employee.company_id == company:
                # Get current attendance state to determine action type
                current_state = employee.attendance_state
                geoip_data = self._get_geoip_portal_response('kiosk')
                
                # If attendance_state is 'checked_out', it means we should check in
                # If attendance_state is 'checked_in', it means we should check out
                if current_state == 'checked_out':
                    # Create new check-in record
                    attendance_vals = {
                        'employee_id': employee.id,
                        'check_in': fields.Datetime.now(),
                    }
                    # Add geolocation data if available
                    if geoip_data.get('latitude') and geoip_data.get('longitude'):
                        attendance_vals.update({
                            'check_in_latitude': geoip_data.get('latitude'),
                            'check_in_longitude': geoip_data.get('longitude'),
                            'check_in_ipaddress': geoip_data.get('ip_address'),
                        })
                    employee.env['hr.attendance'].create(attendance_vals)
                else:
                    # Use standard check-out logic
                    employee.sudo()._attendance_action_change(geoip_data)
                
                return self._get_employee_portal_info(employee)
        return {}
    
    @http.route('/hr_attendance/update_portal_checkin_data', type="json", auth="public")
    def update_portal_checkin_data(self, **kwargs):
        """Update check-in data with geolocation, geofence, photo, and IP information"""
        attendance_id = kwargs.get('attendance_id')
        image = kwargs.get('image')
        check_in_latitude = kwargs.get('check_in_latitude')
        check_in_longitude = kwargs.get('check_in_longitude')
        check_in_geofence_ids = kwargs.get('check_in_geofence_ids')
        check_in_ipaddress = kwargs.get('check_in_ipaddress')

        if not attendance_id:
            return {"error": "Missing attendance_id"}

        attendance = request.env['hr.attendance'].sudo().browse(attendance_id)
        if attendance.exists():
            attendance.sudo().write({
                'check_in_photo': image,
                'check_in_latitude': check_in_latitude,
                'check_in_longitude': check_in_longitude,
                'check_in_geofence_ids': check_in_geofence_ids,
                'check_in_ipaddress': check_in_ipaddress,
            })
        return {"success": True}

    @http.route('/hr_attendance/update_portal_checkout_data', type="json", auth="public")
    def update_portal_checkout_data(self, **kwargs):
        """Update check-out data with geolocation, geofence, photo, and IP information"""
        attendance_id = kwargs.get('attendance_id')
        image = kwargs.get('image')
        check_out_latitude = kwargs.get('check_out_latitude')
        check_out_longitude = kwargs.get('check_out_longitude')
        check_out_geofence_ids = kwargs.get('check_out_geofence_ids')
        check_out_ipaddress = kwargs.get('check_out_ipaddress')

        if not attendance_id:
            return {"error": "Missing attendance_id"}

        attendance = request.env['hr.attendance'].sudo().browse(attendance_id)
        if attendance.exists():
            attendance.sudo().write({
                'check_out_photo': image,
                'check_out_latitude': check_out_latitude,
                'check_out_longitude': check_out_longitude,
                'check_out_geofence_ids': check_out_geofence_ids,
                'check_out_ipaddress': check_out_ipaddress,
            })
        return {"success": True}

    @http.route('/hr_attendance/get_geofence_data', type='json', auth='user')
    def get_geofence_data(self, company_id=None, employee_id=None):
        """Fetch geofence data based on company and employee."""
        if not company_id or not employee_id:
            return {'error': 'Missing company_id or employee_id'}

        geofences = request.env['hr.attendance.geofence'].sudo().search_read(
            domain=[('company_id', '=', int(company_id)), ('employee_ids', 'in', [int(employee_id)])],
            fields=['id', 'name', 'overlay_paths']
        )
        return geofences
        
class PortalAttendanceFaceRecognition(CustomerPortal):
    """Extended portal controller for attendance with face recognition features"""

    def _prepare_home_portal_values(self, counters):
        """Prepare portal home values including attendance count"""
        values = super()._prepare_home_portal_values(counters)
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)],limit=1)
        HrAttendance = request.env['hr.attendance']       
        if 'hr_attendance_count' in counters:
            hr_attendance_count = HrAttendance.sudo().search_count([('employee_id', '=', employee and employee.id or False)])     
            values['hr_attendance_count'] = hr_attendance_count or '0'
        return values
    
    def _prepare_portal_layout_values(self):
        """Prepare portal layout values including attendance state"""
        values = super()._prepare_portal_layout_values()
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)],limit=1)
        values['hr_attendance_state'] = employee.attendance_state
        return values
    
    @http.route(['/my/hr_attendances', '/my/hr_attendances/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_hr_attendances(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='all', **kw):
        """Portal route for displaying employee attendance records"""
        values = self._prepare_portal_layout_values()
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)],limit=1)       
        HrAttendance = request.env['hr.attendance']
        
        domain = [
            ('employee_id', '=', employee and employee.id or False),
        ]
        
        searchbar_sortings = {
            'check_in': {'label': _('Check In'), 'order': 'check_in desc'},
            'check_out': {'label': _('Check Out'), 'order': 'check_out'},
        }
        
        searchbar_inputs = { 
            'check_in': {'input': 'check_in', 'label': _('Search in Check In Date')},
            'check_out': {'input': 'check_out', 'label': _('Search in Check Out Date')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        
        # default sortby order
        if not sortby:
            sortby = 'check_in'
        sort_order = searchbar_sortings[sortby]['order']
               
        today = fields.Date.today()
        quarter_start, quarter_end = date_utils.get_quarter(today)
        last_week = today + relativedelta(weeks=-1)
        last_month = today + relativedelta(months=-1)
        last_year = today + relativedelta(years=-1)
        
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'today': {'label': _('Today'), 'domain': [("check_in", ">=", today),("check_out", "<=", today)]},
            'week': {'label': _('This week'), 'domain': [('check_in', '>=', date_utils.start_of(today, "week")), ('check_out', '<=', date_utils.end_of(today, 'week'))]},
            'month': {'label': _('This month'), 'domain': [('check_in', '>=', date_utils.start_of(today, 'month')), ('check_out', '<=', date_utils.end_of(today, 'month'))]},
            'year': {'label': _('This year'), 'domain': [('check_in', '>=', date_utils.start_of(today, 'year')), ('check_out', '<=', date_utils.end_of(today, 'year'))]},
            'quarter': {'label': _('This Quarter'), 'domain': [('check_in', '>=', quarter_start), ('check_out', '<=', quarter_end)]},
            'last_week': {'label': _('Last week'), 'domain': [('check_in', '>=', date_utils.start_of(last_week, "week")), ('check_out', '<=', date_utils.end_of(last_week, 'week'))]},
            'last_month': {'label': _('Last month'), 'domain': [('check_in', '>=', date_utils.start_of(last_month, 'month')), ('check_out', '<=', date_utils.end_of(last_month, 'month'))]},
            'last_year': {'label': _('Last year'), 'domain': [('check_in', '>=', date_utils.start_of(last_year, 'year')), ('check_out', '<=', date_utils.end_of(last_year, 'year'))]},
        }
        
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        
        # search
        if search and search_in:
            search_domain = []
            if search_in in ('all', 'all'):
                search_domain = OR([search_domain, ['|', ('check_in', 'ilike', search), ('check_out', 'ilike', search)]])
            if search_in in ('check_in', 'all'):
                search_domain = OR([search_domain, [('check_in', 'ilike', search)]])
            if search_in in ('check_out', 'all'):
                search_domain = OR([search_domain, [('check_out', 'ilike', search)]])
            domain += search_domain

        # count for pager
        hr_attendance_count = HrAttendance.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/hr_attendances",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'search_in': search_in, 'search': search},
            total=hr_attendance_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        hr_attendances = HrAttendance.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_hr_attendance_history'] = hr_attendances.ids[:100]
        
        values.update({
            'date': date_begin,
            'hr_attendances': hr_attendances.sudo(),
            'page_name': 'hr_attendances',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
            'default_url': '/my/hr_attendances',
        })
        return request.render("pt_attendance_portal.portal_my_hr_attendances", values)
    
    @http.route(['/my/hr_attendance/<int:attendance_id>'], type='http', auth="public", website=True)
    def portal_my_hr_attendance(self, attendance_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            attendance_sudo = self._document_check_access('hr.attendance', attendance_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if attendance_sudo:
            # store the date as a string in the session to allow serialization
            now = fields.Date.today().isoformat()
            session_obj_date = request.session.get('view_attendance_%s' % attendance_sudo.id)
            if session_obj_date != now and request.env.user.share and access_token:
                request.session['view_hr_attendance_%s' % attendance_sudo.id] = now
                body = _('HR Attendance viewed by Employee %s', attendance_sudo.employee_id.name)
                # In Odoo 18, use message_post directly instead of _message_post_helper
                partner_ids = []
                if attendance_sudo.employee_id.sudo().user_id:
                    partner_ids = attendance_sudo.employee_id.sudo().user_id.partner_id.ids
                attendance_sudo.sudo().with_context(mail_create_nolog=True).message_post(
                    body=body,
                    message_type="notification",
                    subtype_xmlid="mail.mt_note",
                    partner_ids=partner_ids,
                )
        
        values = {
            'hr_attendance': attendance_sudo,
            'token': access_token,
            'bootstrap_formatting': True,
            'employee_id': attendance_sudo.employee_id.id,
            'report_type': 'html',
            'action': attendance_sudo._get_portal_return_action(),
        }
        if attendance_sudo.employee_id.company_id:
            values['res_company'] = attendance_sudo.employee_id.company_id
        
        return request.render('pt_attendance_portal.portal_my_hr_attendance', values)
    
    @http.route(['/my/hr_attendances/create_new'], type='http', auth="user", website=True)
    def create_new_attendance(self, access_token=None):
        if not request.session.uid:
            return {'error': 'anonymous_user'}
        
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)],limit=1)
        reasons = request.env['hr.attendance.reasons'].sudo().search([])
        
        values = {
            'employee': employee,
            'reasons': reasons,
            'page_name': 'create_new_attendance',
        }
        return request.render("pt_attendance_portal.my_attendance_create_new", values)