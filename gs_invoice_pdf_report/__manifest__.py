# -*- coding: utf-8 -*-
{
    'name': "Global Solution Invoice PDF Report",
    'author': "Global Solutions",
    'website': "https://GlobalSolutions.dev",
    'category': 'Uncategorized',

    # any module necessary for this one to work correctly
    # todo gs_partner_customuzaion
    'depends': ['base', 'account'],
    'data': [
        'views/company_arabic_address.xml',
        'views/res_config_settings_views.xml',
        'report/sale_invoice_paper_format.xml',
        'report/custom_header_footer.xml',
        'report/invoice_report_manage.xml',
        'report/invoice_report.xml',
        'report/show_room_report.xml',
        'report/report_style.xml',

    ],
}
