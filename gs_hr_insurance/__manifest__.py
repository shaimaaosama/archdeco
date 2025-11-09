# -*- coding: utf-8 -*-
{
    'name': "GS HR Insurance",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    "author": "Global Solutions",
    "website": "https://globalsolutions.dev",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources/Employees',
    'version': '18.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'gs_hr_employee_updation'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/insurance_contract.xml',
        'views/insurance_network.xml',
        'views/insurance_class.xml',
        'views/follower.xml',
        'views/hr_employee_view.xml',
        'views/insurance.xml',
    ],
    'installable': True,
    'application': True,
}
