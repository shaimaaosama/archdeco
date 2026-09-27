# -*- coding: utf-8 -*-
{
    'name': "Premium Tech HR Payroll Custom",
    'license': 'LGPL-3',
    'summary': "Payroll customizations: batch payment registration, payslip payment ribbons, and payroll journal linking.",
    'description': "Extends Odoo payroll with batch payment registration wizard, payment-state ribbons on payslips, journal entry linkage, and payroll structure assignment on contracts.",
    "author": "Premium Tech",
    "website": "https://ptech.sh",
    'category': 'Human Resources',
    'version': '18.0.1.0.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_payroll', 'hr_payroll_account','pt_hr_contract_allowance'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data2.xml',
        'views/payroll_inherit.xml',
        'views/hr_payroll_report.xml',
        'wizard/register_payment.xml',
    ],

    # only loaded in demonstration mode
    'installable': True,
    'application': True,
}
