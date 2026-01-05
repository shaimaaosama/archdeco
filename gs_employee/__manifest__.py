# -*- coding: utf-8 -*-
{
    'name': "Global Solutions Edit Employee",
    "author": "Global Solutions",
    "website": "https://globalsolutions.dev",
    'category': 'Uncategorized',
    'version': '18.0.1.0',
    'depends': ['base', 'hr', 'gs_hr_employee_updation', 'gs_hr_insurance', 'branch'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/residence_profession.xml',
        'views/type_of_license.xml',
        'views/driving_license_restriction.xml',
        'views/evaluated_by.xml',
        'views/tasks.xml',
        'views/evaluated_by.xml',
        'views/kpi_table.xml',
        'views/bail_type.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
