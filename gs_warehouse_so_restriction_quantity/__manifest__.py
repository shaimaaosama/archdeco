# -*- coding: utf-8 -*-

{
    'name': "gs_warehouse_so_restriction_quantity",
    'author': 'GS Mohammed Alwasefy',
    'category': 'Warehouse',
    'summary': """Display available product's quantity from all warehouse when sales order created""",
    'license': 'AGPL-3',
    'website': 'http://www.odoo.com',
    'description': """
""",
    'version': '1.0',
    'depends': ['sale_management', 'stock', 'sale_stock'],
    'data': [
             'security/ir.model.access.csv',
             'wizard/product_warehouse_quantity.xml',
             'views/sale_view.xml'
    ],
    "qweb": ["static/src/xml/qty_at_date_widget_inherit.xml"],
    'images': ['static/description/banner.png'],
    # 'assets': {
    #     'web.assets_qweb': [
    #         'gs_warehouse_so_restriction_quantity/static/src/xml/**/*',
    #     ],
    # },
    'installable': True,
    'application': True,
    'auto_install': False,
}
