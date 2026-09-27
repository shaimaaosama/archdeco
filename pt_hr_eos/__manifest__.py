# -*- coding: utf-8 -*-
{
    'name': "Premium Tech HR EOS",
    'license': 'LGPL-3',
    'summary': "End of Service calculation and XLSX reporting for Saudi HR operations.",
    'description': "Monthly EOS calculation, EOS benefit configuration, XLSX reports, and automated EOS computation cron for Saudi-compliant employee end-of-service processing.",
    "author": "Premium Tech",
    "website": "https://ptech.sh",
    'category': 'Human Resources',
    'version': '18.0.1.0.0',
    'depends': ['base', 'pt_hr_insurance', 'pt_hr_contract_allowance', 'hr_payroll', 'account_accountant', 'report_xlsx'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'demo/demo.xml',
        'views/end_reason.xml',
        'views/eos.xml',
        'views/res_config_settings.xml',
        'views/eos_monthly.xml',
        'views/eos_conf_view.xml',
        'views/month_eos_xlsx_report.xml',
        'wizard/month_eos_report_wizard.xml',
        'data/cron_jobs.xml',

    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
}
