{
    'name': 'Customer and Vendor Tracking System in Odoo',
    'version': '18.0.0.0',
    'summary': """
            This Customer and Vendor Tracking System module is designed to streamline contact management in Odoo by clearly separating customer and vendor records across the platform. 
            It intelligently filters contacts based on their roles—ensuring that only customers appear in Sales, only vendors in Purchases, and all records are cleanly organized in Invoicing. 
            By eliminating confusion in contact selection, the module enhances operational accuracy and workflow efficiency. b2b customer data platform, customer data platform b2b, invoicing, invoice software, customer database software, client database software, customer database, customer tracking software, customer database platforms, customer database system, customer data software, customer database management, customer database program, customer info, customer data management software, customer information database software, customer tracking system, best customer database software for small business.
            Customer vendor field,b2b customer data platform,customer data platform b2b,invoicing ,invoice software,customer database software,client database software ,customer database,customer tracking software,customer database platforms,customer database system,customer data software,customer database management,customer database program,customer info,customer data management software,customer information database software,customer tracking system,best customer database software for small business
            """,
    'description': """
            This Customer and Vendor Tracking System module is designed to streamline contact management in Odoo by clearly separating customer and vendor records across the platform. 
            It intelligently filters contacts based on their roles—ensuring that only customers appear in Sales, only vendors in Purchases, and all records are cleanly organized in Invoicing. 
            By eliminating confusion in contact selection, the module enhances operational accuracy and workflow efficiency. b2b customer data platform, customer data platform b2b, invoicing, invoice software, customer database software, client database software, customer database, customer tracking software, customer database platforms, customer database system, customer data software, customer database management, customer database program, customer info, customer data management software, customer information database software, customer tracking system, best customer database software for small business.
            Customer vendor field,b2b customer data platform,customer data platform b2b,invoicing ,invoice software,customer database software,client database software ,customer database,customer tracking software,customer database platforms,customer database system,customer data software,customer database management,customer database program,customer info,customer data management software,customer information database software,customer tracking system,best customer database software for small business
            """,
    'author': "Reliution",
    'website': 'https://www.reliution.com/',
    'category': "Sales/CRM",
    "license": "LGPL-3",
    'depends': ['sale', 'purchase','account'],
    'images': ['static/description/banner.gif'],
    'data': [
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/action_view.xml',
        'views/account_payment_views.xml',
        'views/sale_order_default_set_view.xml',
        'views/purchase_order_default_set_view.xml',
    ],
    "installable": True,
    "auto_install": False,
    'application': True,
}