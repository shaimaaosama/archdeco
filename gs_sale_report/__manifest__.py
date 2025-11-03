# -*- coding: utf-8 -*-
{
    'name': "Global Solution Sale Report",
    'author': "Global Solutions",
    'website': "https://GlobalSolutions.dev",
    'category': 'Uncategorized',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','gs_partner_customuzaion'],
    'data': [
        'views/company_arabic_address.xml',
        'report/sale_order_paper_format.xml',
        'report/custom_header_footer.xml',
        'report/sale_order_qutation_report.xml',
        'report/report_style.xml',
    ],
}