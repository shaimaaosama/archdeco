# -*- coding: utf-8 -*-
{
    'name': """Premium Tech End of Service Benefits""",
    'summary': """End Of Service reward for years of services, approvals and disbursements""",
    'description': """Create and Calculate your employees END OF SERVICE Reward""",
    'author': 'Premium Tech',
    'website': 'https://ptech.sh',
    'license': 'LGPL-3',
    'images': ['static/description/Banner.png'],
    'version': '18.0.1.0.0',
    'depends': [ 'base' , 'portal', 'web', 'account', 'account_accountant', 'hr_payroll','pt_hr_contract_allowance',
                'hr_holidays' , 'pt_vacation_settlement'],
    'category': 'Human Resources',
    'data': [
        'data/data.xml',
        'data/types_data.xml',
        'data/sequence.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizards/settlement_views.xml',
        'views/hr_end_service_benefit_views.xml',
        'views/hr_end_service_benefit_type_views.xml',
        'views/hr_employee_views.xml',
        'views/config_views.xml',
        'reports/ending_service_report.xml',
        'reports/end_service_report.xml',
        # 'reports/ending_service_reports/_wizard.xml',
        # 'reports/report_ending_service.xml',

    ],
    'demo': []
}
