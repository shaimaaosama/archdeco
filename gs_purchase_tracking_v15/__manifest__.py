# -*- coding: utf-8 -*-
{
    'name': "gs_purchase_tracking",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'contacts', 'purchase', 'purchase_stock', 'sh_secondary_unit', 'stock'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data2.xml',
        'data/sequence.xml',
        'wizard/receipt_button.xml',
        'views/purchase_tracking.xml',
        'views/purchase_tracking_permission.xml',
        'views/shipment_tracking.xml',
        'views/shipment_documents.xml',
        'views/clearance_documents.xml',
        'report/exterior_purchase_order_report.xml',
        'report/shipment_tracking_report.xml',
    ],
}
