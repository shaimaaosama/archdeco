# -*- coding: utf-8 -*-
{
    'name': "Gs Location",
    "author": "Global Solutions",
    "website": "https://globalsolutions.dev",
    'category': 'Human Resources/Employees',
    'depends': ['base', 'mail', 'stock', 'sh_secondary_unit', 'sgeede_internal_transfer', 'warehouse_stock_restrictions'],
    "images": [
        'static/description/icon.png'
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/get_stock_moves_data.xml',
        'wizard/get_product_moves_data.xml',
        'views/template.xml',
        'views/stock_move_inherit.xml',
        'views/product_move_inherit.xml',
        'security/security.xml',
    ],

    'assets': {
        'web.assets_backend': [
            '/gs_location/static/src/core.css',
            '/gs_location/static/src/js/stock_moves.js',
            '/gs_location/static/src/js/product_moves.js',

        ],
        'web.assets_qweb': [
            '/gs_location/static/src/xml/*.xml',
            '/gs_location/static/src/xml/stock_moves.xml',
        ],
    },

    'qweb': [
        'static/src/xml/*.xml',
        'static/src/xml/stock_moves.xml',
    ],
    'installable': True,
    'application': True,
}
