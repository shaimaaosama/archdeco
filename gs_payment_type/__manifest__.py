# -*- coding: utf-8 -*-
{
    'name': "gs_payment",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'account', 'is_customer_is_vendor'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/payment_inherit.xml',
        'views/payment_type.xml',
        'security/security.xml',
    ],
}
