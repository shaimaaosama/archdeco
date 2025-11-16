# -*- coding: utf-8 -*-
{
    'name': "gs_sales_salesperson_readonly",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'sale', 'account'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'security/security.xml',
        'views/sales_inherit.xml',
    ],
}
