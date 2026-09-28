{
    'name': "Employee Mobile App API",
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Attendances',
    'summary': "REST API backend for the ArchDeco employee mobile app "
               "(login, attendance, geofence, payslips).",
    'description': """
Employee Mobile App API
========================

Exposes a JSON REST API under ``/api/mobile`` so employees can use the
ArchDeco mobile app without needing an Odoo user:

* Login with work email + PIN, token based session (no ``res.users``
  created per employee).
* Server-side geofenced attendance check-in / check-out.
* Attendance history with late / leave detection.
* Payslips (list, detail, PDF download).

Designed to work standalone, and to coexist with ``pt_attendance_portal``
(shares the ``hr.attendance`` geolocation fields, never touches the
portal's own geofence model or routes).
""",
    'author': "Shaimaa Osama El-Marsafawy",
    'license': 'LGPL-3',
    'depends': ['hr', 'hr_attendance', 'hr_payroll', 'resource'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/hr_employee_views.xml',
        'views/hr_work_location_views.xml',
        'views/res_config_settings_views.xml',
        'views/hr_attendance_views.xml',
        'views/mobile_token_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
