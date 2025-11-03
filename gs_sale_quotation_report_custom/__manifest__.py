# -*- coding: utf-8 -*-
{
    'name': "Gs Sale Quotation Report Custom",

    'summary': """
       Custom Quotation Rport""",
    'description': """
        custom quotation report""",

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'sale_management', 'gs_partner_customuzaion', 'gs_stock_from_sr'],
    'data': [
        'security/ir.model.access.csv',
        'views/company_arabic_address.xml',
        'views/views.xml',
        'report/sale_order_paper_format.xml',
        'report/sale_order_qutation_report.xml',
        'report/custom_header_footer.xml',
        'report/report_style.xml',
    ],
}
