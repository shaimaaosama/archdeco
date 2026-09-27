# -*- coding: utf-8 -*-
{
    'name': "Premium Tech HR Insurance",

    'summary': "HR employee medical insurance policy management with follower/dependent tracking.",

    'description': "Manage employee and follower medical insurance policies, insurance classes, networks, policy amounts, active membership, and clearance tracking.",

    "author": "Premium Tech",
    "website": "https://ptech.sh",
    'license': 'LGPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources/Employees',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'pt_hr_employee_updation'],

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
