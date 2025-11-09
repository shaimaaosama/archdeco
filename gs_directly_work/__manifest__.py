# -*- coding: utf-8 -*-
{
    'name': "Gs Directly Work",
    "author": "Global Solutions",
    "website": "https://globalsolutions.dev",
    'category': 'Human Resources/Employees',
    'version': '0.1',
    'depends': ['base', 'gs_hr_insurance'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/directly_work.xml',
    ],
    'installable': True,
    'application': True,
}
