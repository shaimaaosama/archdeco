{
    'name': 'gs_sale_order_custom',
    'depends': ['base', 'account', 'account_accountant', 'sale', 'sale_management'],
    "data": [
        'security/ir.model.access.csv',
        'views/reason.xml',
        'views/sale_order_inherit.xml',
    ],
    'application': True,
    'installable': True,
    'license': 'OPL-1',

}
