# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################
##############################################################################


{
    'name': 'Premium Tech HR Loan',
    'license': 'LGPL-3',
    'version': '18.0.1.0.0',
    'sequence': 1,
    'category': 'Human Resources',
    'summary': 'Employee loan management with installment schedules and payslip deduction integration.',
    'description': """Employee loan lifecycle management: loan requests, installment schedules, payslip deduction integration, loan document tracking, and reporting.""",
    'depends': ['base', 'hr_payroll', 'account', 'pt_hr_insurance', 'pt_hr_payroll_custom', 'l10n_sa_hr_payroll', 'pt_hr_penalties_and_awards'],
#    hr_payroll_account
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/cron.xml',
        'wizard/update_installment_amount.xml',
        'report/employee_loan_template.xml',
        'report/report_menu.xml',
        'views/loan_emi_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_loan_view.xml',
        'views/ir_sequence_data.xml',
        'views/employee_loan_type_views.xml',
        'views/pay_slip_view.xml',
        'views/salary_structure.xml',
        'wizard/import_loan_views.xml',
        'wizard/import_logs_view.xml',
        'wizard/payment_cash.xml',
        'wizard/penalty_cash.xml',
        'views/dev_skip_installment.xml',
        'views/hr_loan_dashbord.xml',
        'views/loan_document.xml',
        'views/loan_report_views.xml',
        'edi/mail_template.xml',
        'edi/skip_installment_mail_template.xml',
        ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    # author and support Details =============#
    "author": "Premium Tech",
    "website": "https://ptech.sh",
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
