# -*- coding: utf-8 -*-
{
    'name': "Premium Tech HR Payroll Reports",
    'license': 'LGPL-3',
    'summary': "Monthly and yearly payroll XLSX reporting for HR and Finance.",
    'description': "Generates payroll analysis reports in XLSX format (monthly and yearly) with payroll amount breakdowns and employee-level totals.",
    "author": "Premium Tech",
    "website": "https://ptech.sh",
    'category': 'Human Resources',
    'version': '18.0.1.0.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_payroll', 'hr', 'hr_work_entry_contract_enterprise', 'account', 'report_xlsx'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/month_salary_xlsx_report.xml',
        'views/year_salary_xlsx_report.xml',
        'wizard/month_salary_report_wizard.xml',
        'wizard/year_salary_report_wizard.xml',
    ],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            '/pt_hr_payroll_report/static/src/less/custom_style.scss'
        ], }
}
