# -*- coding: utf-8 -*-pack
{
    # App information
    'name': 'Auto Reconcile Invoice',
    'category': 'Accounting',
    'version': '18.0.1.0',
    'summary': """Auto Reconcile Invoice, Adds auto reconcile option in Invoicing settings""",
    'description': 'Adds auto reconcile option in Invoicing settings and based on that auto reconcile invoice.',
    'license': 'OPL-1',

    # Dependencies
    'depends': ['account'],

    # Views
    'data': [
       'wizard/res_config_setting.xml',
    ],
    # Odoo Store Specific
    'images': ['static/description/cover.gif'],

    # Author
    'author': 'Vraja Technologies',
    'website': 'http://www.vrajatechnologies.com',
    'maintainer': 'Vraja Technologies',

    # Technical
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',
    'price': '29',
    'currency': 'EUR',

}
# version changelog

