# -*- coding: utf-8 -*-
{
    'name': "gs_purchase_permission",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'purchase', 'purchase_stock'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_permission.xml',
        'views/purchase_inherit.xml',
    ],
}
