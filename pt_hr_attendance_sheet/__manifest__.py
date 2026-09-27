# -*- coding: utf-8 -*-
{
    'name': "Premium Tech Attendance Sheet",

    'summary': "Managing Attendance Sheets and Policies for Employees",
    'description': "Manage employee attendance sheets, overtime, lateness, absence, and payroll-ready batch processing.",
    "author": "Premium Tech",
    "website": "https://ptech.sh",
    'category': 'Human Resources',
    'version': '18.0.1.0.0',
    'images': ['static/description/bannar.jpg'],
    'depends': ['base',
                'hr',
                'hr_payroll',
                'hr_holidays',
                'hr_work_entry_contract',
                'hr_attendance'],
    'data': [
        'data/ir_sequence.xml',
        'data/data2.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/change_att_data_view.xml',
        'views/hr_attendance_sheet_view.xml',
        'views/hr_attendance_policy_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_public_holiday_view.xml',
        'views/attendance_sheet_batch_view.xml',

    ],

    'license': 'LGPL-3',
    'demo': [
        'demo/demo.xml',
    ],
}
