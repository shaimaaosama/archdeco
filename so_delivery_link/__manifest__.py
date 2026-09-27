# -*- coding: utf-8 -*-

{
    'name': "Sale Order and Delivery Link",

    'summary': """ Sale Order and Delivery Link.""",

    'description': """
    """,
    'author': "Hadeel Ali - ArchDeco",
    'license':'OPL-1',	
    'category': 'Warehouse',
    'version': '0.1',
    'depends': ['base', 'stock','sale_stock','sale', 'gs_sale_report', 'gs_sale_quotation_report_custom', 'gs_invoice_pdf_report'],

    'data': [
        'views/stock_picking.xml',
        'reports/report_saleorder.xml',
        'reports/report_invoice.xml',
    ],
    
    
}
