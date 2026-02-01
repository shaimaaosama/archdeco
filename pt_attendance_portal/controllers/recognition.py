from odoo import http
from odoo.http import request
import base64

class HrAttendanceFaceRecognition(http.Controller):
    """Controller for face recognition functionality in attendance system"""
    
    @http.route('/pt_attendance_portal/loadLabeledImages/', type='json', auth='user', website=True)
    def load_labeled_images(self):
        """Load all employee face descriptors for face recognition matching"""
        try:
            descriptions = []
            employees = request.env['hr.employee'].sudo().search([])
            for employee in employees:
                # Only process employees with face recognition enabled
                if not employee.face_recognition_enabled:
                    continue
                    
                descriptors = []
                for faces in employee.user_faces:
                    if faces.descriptor and faces.descriptor != 'false' and faces.descriptor:
                        descriptors.append(faces.descriptor)
                if descriptors:
                    vals = {
                        "label": employee.id,
                        "descriptors": descriptors,
                    }
                    descriptions.append(vals)        
            return descriptions
        except Exception as e:
            import traceback
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error(f"Error loading labeled images: {str(e)}\n{traceback.format_exc()}")
            # Return empty list instead of raising to prevent blocking
            return []

    @http.route('/pt_attendance_portal/getName/<int:employee_id>/', type='json', auth="none")
    def get_name(self,employee_id):
        """Get employee name by ID for face recognition results"""
        name = False
        if employee_id:
            employee = request.env['hr.employee'].sudo().search([('id', '=', int(employee_id))])
            name =  employee.name
        return name