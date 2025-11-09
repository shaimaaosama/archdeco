# -*- coding: utf-8 -*-
{
    'name': "gs_hr_timeoff_report",
    "author": "Global Solutions",
    "website": "https://globalsolutions.dev",
    'category': 'Human Resources/Employees',
    'version': '18.0.1.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_payroll', 'hr', 'hr_work_entry_contract_enterprise', 'account', 'report_xlsx'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/timeoff_xlsx_report.xml',
        'wizard/timeoff_report_wizard.xml',
    ],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            '/gs_hr_timeoff_report/static/src/less/custom_style.scss'
        ], }
}
