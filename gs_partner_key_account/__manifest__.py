# -*- coding: utf-8 -*-
{
    'name': "gs_partner_key_account",
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
        'security/ir.model.access.csv',
        'views/option.xml',
        'views/res_partner_inherit.xml',
    ],

}
