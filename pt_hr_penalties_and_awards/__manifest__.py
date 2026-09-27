# -*- coding: utf-8 -*-
{
    'name': "Premium Tech HR Penalties & Awards",
    'version': '18.0.1.0.0',
    'summary': "Employee penalty and award management with payslip integration and approval workflow.",
    'description': "Manage deductions (penalties) and bonuses (awards) for employees with configurable types, approval flow, and automatic payslip integration.",
    'license': 'LGPL-3',
    "author": "Premium Tech",
    "website": "https://ptech.sh",
    'category': 'Human Resources',
    'depends': ['base', 'pt_hr_insurance', 'pt_hr_contract_allowance', 'hr_payroll', 'hr'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/mail_template.xml',
        'wizard/send_by_email.xml',
        'wizard/update_installment_amount.xml',
        'wizard/register_payment.xml',
        'views/penalties_awards_setting.xml',
        'views/penalties_awards.xml',
        'views/hr_employee_view.xml',
        'views/hr_payslip_view.xml',
        'views/account_journal_view.xml',
        'data/data2.xml',

    ],

    'installable': True,
    'application': True,
}
