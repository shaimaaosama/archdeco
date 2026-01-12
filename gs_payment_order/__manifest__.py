# -*- coding: utf-8 -*-
{
    'name': "GS Payment Order",
    'author': "Global Solutions",
    'website': "http://www.globalsolutions.dev",
    'category': 'Uncategorized',
    'depends': ['base', 'account', 'mail', 'branch', 'helpdesk', 'purchase', 'sale', 'gs_purchase_tracking_v15','analytic_domain_mixin'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/return_wiz.xml',
        'views/payment_type.xml',
        'data/sequence.xml',
        'data/mail_data.xml',
        'wizard/create_payment_button.xml',
        'wizard/special_approval_button.xml',
        'views/payment_order.xml',
        'views/payment_order_permission.xml',
        'views/menu.xml',
        'views/helpdesk_inherit.xml',
        'views/account_payment_inherit.xml',
        'views/res_users_inherit.xml',
        'views/permission_inherit.xml',
        'report/payment_order_report.xml',
    ],

}
