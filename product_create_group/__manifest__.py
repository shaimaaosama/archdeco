{
    'name': 'Product Group Open',
    'Author': 'Ahmed Abd El Baky',
    'depends': ['sale', 'purchase', 'account', 'sale_management', 'gs_sale_quotation_report_custom'],
    'data': [
        'security/security.xml',
        'views/sale_order.xml',
        'views/purchase_order.xml',
        'views/account_move.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
}