# -*- coding: utf-8 -*-
{
    'name': "Gs HR Contract Management",
    "author": "Global Solutions",
    "website": "https://globalsolutions.dev",
    'category': 'Human Resources/Employees',
    'version': '18.0.1.0',
    'depends': ['base', 'sale_management', 'purchase', 'account_accountant', 'hr'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/contact_payment_schedule.xml',
        'views/type_of_contracts.xml',
        'views/contract_management.xml',
        'views/remind.xml',
        'views/subject.xml',
        'views/payments.xml',

    ],

    'installable': True,
    'application': True,
}
