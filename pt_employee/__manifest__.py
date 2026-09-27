# -*- coding: utf-8 -*-
{
    'name': "Premium Tech Employee Data",
    "author": "Premium Tech",
    "website": "https://ptech.sh",
    'license': 'LGPL-3',
    'category': 'Human Resources/Employees',
    'version': '18.0.1.0.0',
    'images': [
        'static/description/icon.png',
    ],
    'depends': ['base', 'hr', 'pt_hr_employee_updation', 'pt_hr_insurance'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/residence_profession.xml',
        'views/type_of_license.xml',
        'views/driving_license_restriction.xml',
        'views/evaluated_by.xml',
        'views/tasks.xml',
        'views/kpi_table.xml',
        'views/bail_type.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
}
