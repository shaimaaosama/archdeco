# -*- coding: utf-8 -*-
{
    'name': "gs_analytic_account_restriction",
    'author': "Global Solutions",
    'website': "http://www.globalsolutions.dev",
    'category': 'Uncategorized',
    'depends': ['base', 'account', 'analytic'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'views/res_user_inherit.xml',
        'security/security.xml',

    ],

}
