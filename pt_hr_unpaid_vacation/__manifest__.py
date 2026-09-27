# -*- coding: utf-8 -*-
{
    'name': "Premium Tech Unpaid Vacation",
    'version': '18.0.1.0.0',
    'summary': "Unpaid leave and no-pay vacation contract integration for Saudi HR operations.",
    'description': "Extends employee contracts with unpaid vacation tracking, integrating with end-of-service benefit accrual calculations.",
    'license': 'LGPL-3',
    "author": "Premium Tech",
    "website": "https://ptech.sh",
    'category': 'Human Resources',
    'depends': ['base', 'hr', 'pt_hr_end_service_benefits', 'hr_work_entry_holidays'],
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
