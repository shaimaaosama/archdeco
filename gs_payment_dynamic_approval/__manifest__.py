# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

{
    "name": "Gs Payment Dynamic Approval",
    'author': "Global Solutions",
    'website': "http://www.globalsolutions.dev",
    "category": "Accounting",
    "depends": ["base", "bus", "gs_payment_order", "gs_base_dynamic_approval"],
    "data": [
        'security/ir.model.access.csv',
        'data/mail_data.xml',
        'views/rejection_wizard.xml',
        'views/gs_payment_approval_line.xml',
        'views/gs_payment_approval_config.xml',
        'views/approval_info.xml',
        'views/gs_payment_order_inherit.xml',
      
        

    ],
    "license": "OPL-1",
    "images": ["static/description/background.png", ],
    "auto_install": False,
    "installable": True,
    "application": True,
    "price": 30,
    "currency": "EUR"
}
