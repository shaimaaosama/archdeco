# -*- coding: utf-8 -*-
{
    'name': "gs_hr_unpaid_vacation",
    "author": "Global Solutions",
    "website": "https://globalsolutions.dev",
    'version': '18.0.1.0',
    'depends': ['base', 'hr', 'hr_end_service_benefits', 'hr_work_entry_holidays'],
    "images": [
        'static/description/icon.png'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/data2.xml',
        'views/hr_contract.xml',
    ],
    'installable': True,
    'application': True,
}
