# -*- coding: utf-8 -*-
{
    'name': 'Custom Deferred Accounts per Product',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Specify deferred accounts on products',
    'description': """
        This module allows users to define specific Deferred Expense/Revenue accounts 
        and their P&L counterparts on the Product Template.
    """,
    'author': 'Ahmed Abd El Baky',
    'depends': ['account_accountant', 'product'],
    'data': [
        'views/product_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
