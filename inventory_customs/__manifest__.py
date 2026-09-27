# -*- coding: utf-8 -*-

{
    'name': "Inventory Customizations",

    'summary': """Inventory Customizations""",

    'description': """
    - Link Delivery with Sales Order.
    - Invoice Tax Incl and Excl Format.
    - Purchase Excel Report.
    - Inventory Aging Detailed.
    - Inventory Aging Summary.
    """,
    'author': "Hadeel Ali - ArchDeco",
    'license':'OPL-1',	
    'category': 'Warehouse',
    'version': '0.1',
    'depends': ['base', 'stock','sale_stock','sale', 'purchase_stock', 'report_xlsx','gs_sale_report', 'gs_sale_quotation_report_custom', 'gs_invoice_pdf_report'],

    'data': [
        'security/ir.model.access.csv',
        'security/security_view.xml',

        'views/stock.xml',

        'reports/report_saleorder.xml',
        'reports/report_invoice.xml',
        'reports/purchase_excel_report.xml',
        'reports/inventory_aging.xml'
    ],

    'assets': {
        'web.assets_backend': [
            'inventory_customs/static/src/inventory_aging/inventory_aging.js',
            'inventory_customs/static/src/inventory_aging/inventory_aging.xml',
            'inventory_customs/static/src/inventory_aging/inventory_aging.scss',
        ],
    },
    
}
