# -*- coding: utf-8 -*-
{
    'name': "gs_inventory_restrict_report",
    "author": "Global Solutions",
    "website": "https://globalsolutions.dev",
    'category': 'Human Resources/Employees',
    'version': '0.1',
    'depends': ['base', 'mail', 'account', 'warehouse_stock_restrictions'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'security/security.xml',
    ],

    'installable': True,
    'application': True,
}
