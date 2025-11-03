# -*- coding: utf-8 -*-
{
    'name': "gs_crm_custom",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'depends': ['base', 'crm', 'project'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/crm_inherit.xml',
        'report/report_manage.xml',
        'report/crm_report.xml',
        'report/crm_header.xml',
        'report/report_style.xml',
    ],
}
