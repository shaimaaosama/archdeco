# -*- coding: utf-8 -*-
{
    'name': "gs_inventory_permission",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'depends': ['base', 'stock', 'sgeede_internal_transfer', 'stock_account'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/inventory_permission.xml',
        'views/inventory_inherit.xml',
    ],
}
