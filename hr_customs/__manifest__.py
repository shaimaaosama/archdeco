# -*- coding: utf-8 -*-

{
    'name': "HR Customizations",

    'summary': """ HR Customizations""",

    'description': """
    - Attendances Dashboard.
    """,
    'author': "Hadeel Ali - ArchDeco",
    'license':'OPL-1',	
    'category': 'Accounts',
    'version': '0.1',
    'depends': ['base', 'hr_attendance', 'pt_hr_contract_allowance'],

    'data': [
        'security/security_view.xml',

        'views/working_schedules.xml',

        'reports/attendance_dashboard.xml',

    ],

    'assets': {
        'web.assets_backend': [
            'hr_customs/static/src/**/*',
        ],
    },
    
    
}
