# -*- coding: utf-8 -*-
{
    'name': "gs_stock_card_report",
    'author': "Global Solutions",
    'website': "http://www.globalsolutions.dev",
    'category': 'Uncategorized',
    'depends': ['base', 'stock', 'mail', 'gs_product_brand', 'gs_location', 'report_xlsx'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/stock_card_report.xml',
        'views/stock_card_xlsx_report.xml',
        'wizard/stock_card_wizard.xml',
    ],
}
