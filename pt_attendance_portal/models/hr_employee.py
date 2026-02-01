from odoo import fields, models, api, _

class HrEmployee(models.Model):
    _inherit = "hr.employee"
    
    # Face recognition images for this employee
    user_faces = fields.One2many("hr.employee.faces", "employee_id", "Faces")
    face_recognition_enabled = fields.Boolean("Enable Face Recognition", default=False, help="Enable face recognition for this employee")
    
    # MAC address device management
    allowed_devices = fields.One2many("hr.employee.allowed.device", "employee_id", "Allowed Devices")
    allow_next_device = fields.Boolean("Allow Next Device", help="If checked, the next device used for attendance will be automatically added to allowed devices")
    device_check_enabled = fields.Boolean("Enable Device Check", default=True, help="If enabled, only allowed devices can be used for attendance")
    
    # Override attendance state to ensure first attendance of day is always check-in
    attendance_state = fields.Selection([
        ('checked_in', 'Checked in'),
        ('checked_out', 'Checked out')
    ], compute='_compute_attendance_state', store=True, help="Current attendance state")
    
    @api.depends('last_attendance_id.check_in', 'last_attendance_id.check_out')
    def _compute_attendance_state(self):
        """Override attendance state computation to ensure first attendance of day is always check-in"""
        for employee in self:
            if not employee.last_attendance_id:
                employee.attendance_state = 'checked_out'
                continue
                
            last_attendance = employee.last_attendance_id
            
            # Check if the last attendance was today
            today = fields.Date.today()
            last_attendance_date = last_attendance.check_in.date() if last_attendance.check_in else None
            
            # If last attendance was not today, always show check-in for first attendance of the day
            if last_attendance_date != today:
                employee.attendance_state = 'checked_out'
            else:
                # If last attendance was today, use standard logic
                if last_attendance.check_out:
                    employee.attendance_state = 'checked_out'
                else:
                    employee.attendance_state = 'checked_in'
    
    def attendance_action(self):
        """Override attendance action to handle first check-in of day logic"""
        self.ensure_one()
        
        # Check if we need to create a new attendance for first check-in of day
        if self.attendance_state == 'checked_out':
            # Standard check-in logic
            return super().attendance_action()
        else:
            # Check if last attendance was from a previous day
            if self.last_attendance_id:
                today = fields.Date.today()
                last_attendance_date = self.last_attendance_id.check_in.date() if self.last_attendance_id.check_in else None
                
                # If last attendance was not today and was a check-in, create new attendance for check-out
                if last_attendance_date != today and not self.last_attendance_id.check_out:
                    # Create a new attendance record for today's check-in
                    attendance_vals = {
                        'employee_id': self.id,
                        'check_in': fields.Datetime.now(),
                    }
                    new_attendance = self.env['hr.attendance'].create(attendance_vals)
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    }
            
            # Standard check-out logic
            return super().attendance_action()
    
class HrEmployeeFaces(models.Model):
    """Model for storing employee face recognition data and descriptors"""
    _name = "hr.employee.faces"
    _description = "Face Recognition Images"
    _inherit = ['image.mixin']
    _order = 'id'

    # Employee name for display
    name = fields.Char("Name", related='employee_id.name')
    
    # Face image data
    image = fields.Binary("Images")
    
    # Face recognition descriptor (JSON format)
    descriptor = fields.Text(string='Face Descriptor')
    
    # Flag to indicate if face descriptor exists
    has_descriptor = fields.Boolean(string="Has Face Descriptor",default=False, compute='_compute_has_descriptor', readonly=True, store=True)
    
    # Employee relationship
    employee_id = fields.Many2one("hr.employee", "User", index=True, ondelete='cascade')

    @api.depends('descriptor')
    def _compute_has_descriptor(self):
        """Compute whether face descriptor exists for this record"""
        for rec in self:
            rec.has_descriptor = True if rec.descriptor else False


class HrEmployeeAllowedDevice(models.Model):
    """Model for managing allowed devices for employees"""
    _name = "hr.employee.allowed.device"
    _description = "Employee Allowed Device"
    _order = 'create_date desc'

    name = fields.Char("Device Name", required=True)
    mac_address = fields.Char("MAC Address", required=True, help="MAC address of the device")
    device_type = fields.Selection([
        ('desktop', 'Desktop'),
        ('laptop', 'Laptop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('other', 'Other')
    ], string="Device Type", default='other')
    is_active = fields.Boolean("Active", default=True)
    employee_id = fields.Many2one("hr.employee", "Employee", required=True, index=True, ondelete='cascade')
    last_used = fields.Datetime("Last Used", readonly=True)
    notes = fields.Text("Notes")

    _sql_constraints = [
        ('unique_mac_employee', 'unique(mac_address, employee_id)', 'MAC address must be unique per employee!')
    ]

    @api.model
    def create(self, vals):
        # Normalize MAC address format
        if vals.get('mac_address'):
            vals['mac_address'] = self._normalize_mac_address(vals['mac_address'])
        return super().create(vals)

    def write(self, vals):
        # Normalize MAC address format
        if vals.get('mac_address'):
            vals['mac_address'] = self._normalize_mac_address(vals['mac_address'])
        return super().write(vals)

    def _normalize_mac_address(self, mac_address):
        """Normalize MAC address to standard format (XX:XX:XX:XX:XX:XX)"""
        if not mac_address:
            return mac_address
        
        # Remove all non-hex characters
        mac = ''.join(c for c in mac_address.upper() if c in '0123456789ABCDEF')
        
        # Ensure it's 12 characters (6 bytes)
        if len(mac) != 12:
            return mac_address  # Return original if invalid
        
        # Format as XX:XX:XX:XX:XX:XX
        return ':'.join(mac[i:i+2] for i in range(0, 12, 2))

    def check_device_access(self, employee_id, mac_address):
        """Check if the device is allowed for the employee"""
        normalized_mac = self._normalize_mac_address(mac_address)
        
        # Check if device check is enabled for the employee
        employee = self.env['hr.employee'].browse(employee_id)
        if not employee.device_check_enabled:
            return True, None
        
        # Check if device is in allowed devices
        allowed_device = self.search([
            ('employee_id', '=', employee_id),
            ('mac_address', '=', normalized_mac),
            ('is_active', '=', True)
        ], limit=1)
        
        if allowed_device:
            # Update last used timestamp
            allowed_device.write({'last_used': fields.Datetime.now()})
            return True, allowed_device
        
        return False, None

    def add_device_from_attendance(self, employee_id, mac_address, device_name=None, device_type=None):
        """Add a new device from attendance attempt"""
        normalized_mac = self._normalize_mac_address(mac_address)
        
        # Check if device already exists
        existing_device = self.search([
            ('employee_id', '=', employee_id),
            ('mac_address', '=', normalized_mac)
        ], limit=1)
        
        if existing_device:
            # Reactivate if inactive and update device type if provided
            update_vals = {
                'is_active': True,
                'last_used': fields.Datetime.now()
            }
            if device_type and device_type in ['desktop', 'laptop', 'mobile', 'tablet', 'other']:
                update_vals['device_type'] = device_type
            existing_device.write(update_vals)
            return existing_device
        
        # Create new device
        device_vals = {
            'employee_id': employee_id,
            'mac_address': normalized_mac,
            'name': device_name or f"Device {normalized_mac}",
            'last_used': fields.Datetime.now()
        }
        
        # Set device type if provided and valid
        if device_type and device_type in ['desktop', 'laptop', 'mobile', 'tablet', 'other']:
            device_vals['device_type'] = device_type
        
        return self.create(device_vals)