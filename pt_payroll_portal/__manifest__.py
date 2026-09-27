
{
    'name': 'Portal Payslip',
    'sequence': '12',
    "version": "18.1",
    'category': 'Human Resources/Payroll',
    'summary': 'Allow employees to view and download payslips from portal',
    'description': """
        Portal Payslip Access
        =====================
        This module allows portal users to:
        - View their payslips
        - Download payslip PDFs
        - Access payslip history
    """,
    "author": "CodersFort Info Solutions",
    "maintainer": "CodersFort Info Solutions",
    "license": "Other proprietary",
    "website": "https://www.codersfort.com",
    "images": ["images/pt_payroll_portal.png"],
    'depends': [
        'hr_payroll',
        'portal',
        'hr',
    ],
    'data': [
        'security/portal_payslip_security.xml',
        'security/ir.model.access.csv',
        'views/portal_payslip_templates.xml',
        'views/hr_payslip_views.xml',
        'views/report_payslip_templates.xml',
    ],
    "installable": True,
    "application": True,
    "price": 0.0,
    "currency": "EUR",
}