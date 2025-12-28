# -*- coding: utf-8 -*-
{
    'name': "gs_partner_type_class",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'account', 'branch'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/partner_type.xml',
        'views/partner_class.xml',
        'views/res_partner_inherit.xml',
        # 'security/security.xml',
    ],

}
