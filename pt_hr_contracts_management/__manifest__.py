# -*- coding: utf-8 -*-
{
    'name': "Premium Tech Contract Management",
    'license': 'LGPL-3',
    "author": "Premium Tech",
    "website": "https://ptech.sh",
    'category': 'Human Resources/Employees',
    'version': '18.0.1.0.0',
    'depends': ['base', 'sale_management', 'purchase', 'account_accountant', 'account_asset', 'hr'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'data/ir_sequence.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
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
