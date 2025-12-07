# -*- coding: utf-8 -*-
{
    'name': "gs_payment_term_restriction",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'account'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',,
        'views/res_users_inherit.xml',
        'security/security.xml',
    ],

}
