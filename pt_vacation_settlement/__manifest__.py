# -*- coding: utf-8 -*-
{
    'name': "Premium Tech Vacation Settlement",
    'version': '18.0.1.0.0',
    'summary': "HR vacation settlement workflow with approval, calculation, and document generation.",
    'description': "Manages the complete vacation settlement lifecycle: request submission, approval, leave-balance calculation, allowance payout, and printed settlement document.",
    'author': "Premium Tech",
    'website': "https://ptech.sh",
    'category': 'Human Resources',
    'depends': ['hr','pt_employee','pt_hr_insurance','pt_hr_contract_allowance','account','pt_time_off_custom'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/employee_vacation_settlement_data.xml',
        'views/hr_vacation_settlement.xml',
        'views/type_allowances_setting.xml',
        'report/custom_header_footer.xml',
        'report/report_vacation.xml',
        'report/report.xml',
    ],
    'license': 'LGPL-3',
    "pre_init_hook": None,
    "post_init_hook": None,
}
