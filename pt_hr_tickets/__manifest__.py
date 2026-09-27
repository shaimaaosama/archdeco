# -*- coding: utf-8 -*-
{
    'name': "Premium Tech HR Tickets",
    'version': '18.0.1.0.0',
    'summary': "HR travel and flight ticket management for employee entitlements and requests.",
    'description': "Manage employee flight ticket entitlements: ticket requests, approvals, ticket type configuration, and integration with insurance and HR records.",
    'license': 'LGPL-3',
    "author": "Premium Tech",
    "website": "https://ptech.sh",
    'category': 'Human Resources',
    'depends': ['base', 'pt_hr_insurance'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/tickets.xml',
    ],
    'installable': True,
    'application': True,
}
