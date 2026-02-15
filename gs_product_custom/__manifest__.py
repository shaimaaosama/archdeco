# -*- coding: utf-8 -*-
{
    'name': "gs_product_custom",
    'author': "Global Solutions",
    'website': "https://www.globalsolutions.dev",
    'category': 'Uncategorized',
    'depends': ['base', 'product', 'sale','account_accountant'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'views/product_inherit.xml',
        'security/security.xml',
    ],
}
