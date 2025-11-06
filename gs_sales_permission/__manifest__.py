# -*- coding: utf-8 -*-
{
    'name': "gs_sales_permission",
    'author': "Global Solutions",
    'website': "https://GlobalSolutions.dev",
    'category': 'Uncategorized',
    'depends': ['base', 'sale', 'gs_stock_from_sr', 'quotation_revision', 'gs_customer_credit_limit'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/sales_permission.xml',
        'views/sales_inherit.xml',
    ],
}
