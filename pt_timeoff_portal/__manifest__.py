{
    "name": "Employee Time Off Portal (Employee Leave Portal)",
    "summary": "This module is to allow the Portal users can manage Time Off request from Portal User Account.",
    "version": "18.1",
    "description": """This module is to allow the Portal users can manage Time Off request from Portal User Account.""",    
    "author": "Premium Tech",
    "maintainer": "Premium Tech",
    "license" :  "Other proprietary",
    "website": "https://ptech.sh",
    "images": ["images/pt_timeoff_portal.png"],
    "category": "Portal",
    "depends": [
        "website",
        "portal",
        "mail",
        "hr",
        "hr_holidays",
        "gs_time_off_custom",
    ],
    "data": [
    	'security/ir.model.access.csv',
        "views/hr_employee_views.xml",
        "views/hr_leave_portal_templates.xml",
        "views/hr_leave_type.xml",

    ],
    "assets": {
        "web.assets_frontend": [
            "/pt_timeoff_portal/static/src/js/timeoff_portal.js",
            "/pt_timeoff_portal/static/src/css/style.css",
        ]
    },
    "qweb": [],
    "installable": True,
    "application": True,
    "price"                :  85,
    "currency"             :  "EUR",
    # "pre_init_hook"        :  "pre_init_check",
}
