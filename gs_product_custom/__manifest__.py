# -*- coding: utf-8 -*-
{
    'name': "gs_product_custom",
    'author': "Global Solutions",
    'website': "https://www.globalsolutions.dev",
    'category': 'Uncategorized',
    'depends': ['base', 'product', 'sale'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_inherit.xml',
    ],
}
