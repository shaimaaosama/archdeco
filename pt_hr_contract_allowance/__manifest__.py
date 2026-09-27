# -*- coding: utf-8 -*-
{
    'name': "Premium Tech HR Contract Allowance",
    'license': 'LGPL-3',

    'summary': "Employee contract allowances with multi-type configuration, payroll integration, and approval workflow.",
    'description': "Defines and manages employee allowance types on contracts (Housing, Transport, Social, etc.) with payroll salary rule integration, collection, and approval support.",

    "author": "Premium Tech",
    "website": "https://ptech.sh",
    'category': 'Human Resources',
    'version': '18.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_holidays', 'hr_contract', 'account', 'contacts', 'hr_payroll', 'pt_hr_saudi_gosi', 'pt_hr_insurance', 'l10n_sa_hr_payroll'],

    # always loaded
    'data': [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'views/contract_allowance.xml',
        'views/allowances_collection.xml',
        'views/allowances.xml',
        'views/template.xml',
        'views/enrol_employee.xml',
        'views/hr_employee_inherit.xml',
        'demo/payslip_rules.xml',
        'demo/demo.xml',
        'views/contract_duration.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pt_hr_contract_allowance/static/src/css/style.css',
        ],
    },
    'installable': True,
    'application': True,
}
