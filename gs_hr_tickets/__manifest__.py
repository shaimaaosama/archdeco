# -*- coding: utf-8 -*-
{
    'name': "Gs HR Tickets",
    "author": "Global Solutions",
    "website": "https://globalsolutions.dev",
    'category': 'Human Resources/Employees',
    'version': '18.0.1.0',
    'depends': ['base', 'gs_hr_insurance'],
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
