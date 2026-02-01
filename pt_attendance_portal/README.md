# PT Attendance Portal - Odoo 18 Module

## Overview

PT Attendance Portal is a comprehensive Odoo 18 module that extends the standard HR attendance system with advanced features including geolocation tracking, geofencing, face recognition, photo capture, IP address tracking, and attendance reasons. This module provides both portal and kiosk interfaces for employee attendance management.

## Features

### Core Features
- **Geolocation Tracking**: Capture and store GPS coordinates for check-in/out locations
- **Geofencing**: Define virtual geographic boundaries for attendance locations
- **Face Recognition**: Advanced face recognition using face-api.js library
- **Photo Capture**: Manual photo capture during attendance
- **IP Address Tracking**: Record IP addresses for security and audit purposes
- **Attendance Reasons**: Define and track reasons for check-in/out actions

### Interface Modes
- **Portal Mode**: Web-based interface for employees to manage their attendance
- **Kiosk Mode**: Public interface for attendance terminals
- **Manual Selection**: Support for manual employee selection

### Security Features
- Access token-based authentication for portal access
- Company-specific geofence assignments
- Employee-specific feature permissions
- Secure face descriptor storage

## Installation

### Prerequisites
- Odoo 18.0 or higher
- Python 3.10+
- Required dependencies (automatically installed):
  - face-api.js (included in static assets)
  - OpenLayers (ol-6.12.0) for map functionality
  - SweetAlert2 for enhanced UI notifications

### Installation Steps
1. Copy the `pt_attendance_portal` module to your Odoo addons directory
2. Update the addons list in Odoo
3. Install the module from the Apps menu
4. Configure company settings for desired features

## Configuration

### Company Settings
Navigate to **Settings > General Settings > Attendance Portal** to configure:

#### Feature Flags
- **Geolocation**: Enable GPS coordinate tracking
- **Geofence**: Enable virtual boundary enforcement
- **Face Recognition**: Enable face recognition (excludes photo mode)
- **Photo**: Enable photo capture (excludes face recognition)
- **IP Address**: Enable IP address tracking
- **Reason**: Enable attendance reason tracking

#### Mode-Specific Settings
- **Kiosk Mode**: Settings for public attendance terminals
- **Portal Mode**: Settings for employee portal access

#### Attendance Mode
- **Barcode/RFID**: Traditional barcode/RFID scanning
- **Barcode/Manual**: Combined barcode, face recognition, and manual selection
- **Manual**: Manual employee selection only

### Geofence Configuration
1. Navigate to **HR > Attendance > Geofences**
2. Create new geofence areas with:
   - Name and description
   - Geographic boundary coordinates (JSON format)
   - Assigned employees
   - Company association

### Face Recognition Setup
1. Navigate to **HR > Employees**
2. Select an employee
3. Add face images in the "Faces" tab
4. The system will generate face descriptors automatically

## Usage

### Employee Portal Access
1. Employees can access their attendance portal at `/my/hr_attendances`
2. View attendance history with filtering and sorting options
3. Check-in/out with enabled features (geolocation, photos, reasons, etc.)

### Kiosk Mode
1. Access the public kiosk interface
2. Employees can check-in/out using:
   - Barcode/RFID scanning
   - Face recognition
   - Manual selection
3. All configured features are enforced during attendance actions

### Attendance Management
- **Geolocation**: Automatically captured from browser GPS or IP geolocation
- **Geofence Validation**: Ensures attendance within defined boundaries
- **Face Recognition**: Real-time face matching against stored descriptors
- **Photo Capture**: Manual photo capture with webcam
- **Reason Tracking**: Select from predefined reasons for attendance actions

## Technical Architecture

### Models
- `hr.attendance`: Extended with geolocation, geofence, photo, IP, and reason fields
- `hr.attendance.geofence`: Virtual geographic boundaries
- `hr.employee.faces`: Face recognition data storage
- `hr.attendance.reasons`: Attendance reason definitions
- `res.company`: Company-specific feature configurations

### Controllers
- `PortalAttendanceFacerecognitionController`: Portal attendance operations
- `PortalAttendanceFaceRecognition`: Extended portal functionality
- `HrAttendance`: Enhanced attendance controller
- `HrAttendanceFaceRecognition`: Face recognition API endpoints

### Assets
- **Frontend**: JavaScript libraries for face recognition, mapping, and UI enhancements
- **Backend**: Enhanced attendance views and geofence management interface
- **Public**: Kiosk mode assets and public attendance interface

## API Endpoints

### Public Endpoints
- `/hr_attendance/portal_manual_selection`: Manual employee selection
- `/hr_attendance/update_portal_checkin_data`: Update check-in data
- `/hr_attendance/update_portal_checkout_data`: Update check-out data
- `/pt_attendance_portal/loadLabeledImages/`: Load face recognition data
- `/pt_attendance_portal/getName/<employee_id>/`: Get employee name

### User Endpoints
- `/my/hr_attendances`: Employee attendance portal
- `/pt_attendance_portal/search_read/get_employee_data`: Employee data retrieval
- `/hr_attendance/get_geofence_data`: Geofence data retrieval

## Security Considerations

- All sensitive operations require proper authentication
- Face descriptors are stored securely and not exposed directly
- Geofence data is validated server-side
- IP addresses are logged for audit purposes
- Access tokens provide secure portal access

## Troubleshooting

### Common Issues
1. **Face Recognition Not Working**: Ensure face-api.js is loaded and face descriptors exist
2. **Geolocation Errors**: Check browser permissions and GPS availability
3. **Geofence Validation Fails**: Verify geofence coordinates and employee assignments
4. **Portal Access Issues**: Check access tokens and user permissions

### Debug Mode
Enable debug mode in Odoo to view detailed error messages and API responses.

## Support

For technical support and feature requests, please contact Premium Tech.

## License

This module is proprietary software. All rights reserved by Premium Tech.

## Version History

- **18.0.0**: Upgraded to Odoo 18
  - Updated view definitions (tree → list)
  - Migrated conditional attributes to modifiers format
  - Improved compatibility with Odoo 18 architecture
- **17.1**: Initial release for Odoo 17
  - Geolocation tracking
  - Geofencing support
  - Face recognition integration
  - Portal and kiosk interfaces
  - Comprehensive attendance management
