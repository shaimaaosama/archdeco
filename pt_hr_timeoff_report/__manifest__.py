# -*- coding: utf-8 -*-
{
    'name': "Premium Tech HR Time Off Reports",
    'license': 'LGPL-3',
    'summary': "XLSX reporting for employee time off balances and periods.",
    'description': "Provides exportable XLSX reports for employee time off records, balances, and period-based leave analytics.",
    "author": "Premium Tech",
    "website": "https://ptech.sh",
    'category': 'Human Resources',
    'version': '18.0.1.0.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_payroll', 'hr', 'hr_holidays', 'hr_work_entry_contract_enterprise', 'account', 'report_xlsx'],
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
            '/pt_hr_timeoff_report/static/src/less/custom_style.scss'
        ], }
}
