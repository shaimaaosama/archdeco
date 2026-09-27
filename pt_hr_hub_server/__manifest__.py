# -*- coding: utf-8 -*-
{
    "name": "Premium Tech HR Hub Server",
    "version": "18.0.1.0.0",
    "summary": "Multi-tenant attendance hub for mobile app and client Odoo sync.",
    "description": "Receives mobile attendance events through MuK REST, validates device and FaceIO token, and asynchronously synchronizes attendance to client Odoo instances through XML-RPC.",
    "license": "LGPL-3",
    "author": "Premium Tech",
    "website": "https://ptech.sh",
    "category": "Human Resources",
    "depends": ["base", "hr", "hr_attendance", "muk_rest"],
    "data": [
        "security/ir.model.access.csv",
        "views/hub_client_config_views.xml",
        "views/hr_employee_views.xml",
        "views/faceio_settings_views.xml",
        "views/faceio_enrollment_page.xml",
        "views/faceio_kiosk_page.xml",
        "data/ir_cron.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "pt_hr_hub_server/static/src/js/faceio_enrollment_action.js",
            "pt_hr_hub_server/static/src/xml/faceio_enrollment_action.xml",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
