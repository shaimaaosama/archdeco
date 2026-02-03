{
    "name": """
        HR Attendance Control | Attendance Face recognition | Attendance Geolocation |
        Attendance Geofence | Attendance IP Address
    """,
    "summary": """
        This module allows the odoo Hr Attendance Manager / Administrators to define a virtual geographic boundary for 
        attendance locations, and employees can only check in and out within one of these Geofence areas. Additionally, 
        the module will record employee geolocation, geofence, face rRecognition with photo, IP address, and check in/out reasons.
    """,
    "version": "18.0.0.1",
    "description": """
        This module allows the odoo Hr Attendance Manager / Administrators to define a virtual geographic boundary for 
        attendance locations, and employees can only check in and out within one of these Geofence areas. Additionally, 
        the module will record employee geolocation, geofence, face rRecognition with photo, IP address, and check in/out reasons.
        Geolocation
        Geofence 
        Photo   
        IP Address
        Check In - Check Out Reasons
        Face Recognition
    """,    
    "author": "Premium Tech",
    "maintainer": "Premium Tech",
    "contributors": [
        "Ameer Essam <ameer.essama@gmail.com>",
    ],
    "license" :  "Other proprietary",
    "website": "https://ptech.sh",
    "images": ["images/pt_attendance_portal.png"],
    "category": "Human Resources",
    "depends": [
        "base",
        "hr_attendance",
        "portal",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/geolocation_data.xml",
        "views/res_config_settings.xml",
        "views/hr_attendance_reasons_view.xml",
        "views/hr_attendance_geofence.xml",
        "views/hr_attendance_views.xml",
        "views/hr_employee_views.xml",   
        "views/portal_templates.xml.xml",     
    ],
    "assets": {
        "web.assets_backend": [
            # Note: face-api.js is loaded dynamically via script tags, not as a module
            # Ol Steet Map
            "/pt_attendance_portal/static/src/lib/ol-6.12.0/ol.css",
            "/pt_attendance_portal/static/src/lib/ol-ext/ol-ext.css",
            "/pt_attendance_portal/static/src/lib/ol-6.12.0/ol.js",
            "/pt_attendance_portal/static/src/lib/ol-ext/ol-ext.js",

            "/pt_attendance_portal/static/src/js/attendance_menu.js",
            "/pt_attendance_portal/static/src/js/attendance_menu.scss",
            "/pt_attendance_portal/static/src/js/attendance_menu.xml",
            "/pt_attendance_portal/static/src/js/attendance_recognition_dialog.js",
            "/pt_attendance_portal/static/src/js/attendance_recognition_dialog.xml",
            "/pt_attendance_portal/static/src/css/face_recognition_dialog.css",
            "/pt_attendance_portal/static/src/js/attendance_webcam_dialog.js",
            "/pt_attendance_portal/static/src/js/attendance_webcam_dialog.xml",
            "/pt_attendance_portal/static/src/js/field_one2many_descriptor.js",
            "/pt_attendance_portal/static/src/css/face_recognition.css",
            "/pt_attendance_portal/static/src/js/geofence_arch_parser.js",
            "/pt_attendance_portal/static/src/js/geofence_controller.js",
            "/pt_attendance_portal/static/src/js/geofence_controller.xml",
            "/pt_attendance_portal/static/src/js/geofence_drawing.js",
            "/pt_attendance_portal/static/src/js/geofence_drawing.css",
            "/pt_attendance_portal/static/src/js/geofence_drawing.xml",
            "/pt_attendance_portal/static/src/js/geofence_model.js",
            "/pt_attendance_portal/static/src/js/geofence_renderer.js",
            "/pt_attendance_portal/static/src/js/geofence_renderer.xml",
            "/pt_attendance_portal/static/src/js/geofence_view.js",

            "/pt_attendance_portal/static/src/js/image_webcam_dialog.js",
            "/pt_attendance_portal/static/src/js/image_webcam_dialog.xml",
            "/pt_attendance_portal/static/src/js/image_webcam.js",
            "/pt_attendance_portal/static/src/js/image_webcam.xml",
        ],
        "web.assets_frontend": [
            # Note: face-api.js is loaded dynamically via script tags, not as a module
            # Ol Steet Map
            "/pt_attendance_portal/static/src/lib/ol-6.12.0/ol.css",
            "/pt_attendance_portal/static/src/lib/ol-ext/ol-ext.css",
            "/pt_attendance_portal/static/src/lib/ol-6.12.0/ol.js",
            "/pt_attendance_portal/static/src/lib/ol-ext/ol-ext.js",
            
            "/pt_attendance_portal/static/src/css/portal.css",
            "/pt_attendance_portal/static/src/css/attendance_animations.css",
            "/pt_attendance_portal/static/src/lib/sweetalert2/sweetalert2.css",
            "/pt_attendance_portal/static/src/lib/sweetalert2/sweetalert2.js",
            "/pt_attendance_portal/static/src/js/portal_attendance.js",

            "/pt_attendance_portal/static/src/js/attendance_recognition_dialog.js",
            "/pt_attendance_portal/static/src/js/attendance_recognition_dialog.xml",
            "/pt_attendance_portal/static/src/css/face_recognition_dialog.css",
        ],
        "hr_attendance.assets_public_attendance":[
            # Note: face-api.js is loaded dynamically via script tags, not as a module
            # Ol Steet Map
            "/pt_attendance_portal/static/src/lib/ol-6.12.0/ol.css",
            "/pt_attendance_portal/static/src/lib/ol-ext/ol-ext.css",
            "/pt_attendance_portal/static/src/lib/ol-6.12.0/ol.js",
            "/pt_attendance_portal/static/src/lib/ol-ext/ol-ext.js",

            "/pt_attendance_portal/static/src/js/attendance_recognition_dialog.js",
            "/pt_attendance_portal/static/src/js/attendance_recognition_dialog.xml",
            "/pt_attendance_portal/static/src/css/face_recognition_dialog.css",
            "/pt_attendance_portal/static/src/js/public_kiosk_app.scss",
            "/pt_attendance_portal/static/src/js/public_kiosk_app.js",
            "/pt_attendance_portal/static/src/js/public_kiosk_app.xml",
        ]
    },   
    "installable": True,
    "application": True,
    "price"                 :  650.00,
    "currency"              :  "EUR",
    "pre_init_hook"         :  "pre_init_check",
    'uninstall_hook': 'uninstall_hook',
}
