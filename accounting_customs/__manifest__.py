# -*- coding: utf-8 -*-

{
    'name': "Accounting Customizations",

    'summary': """ Accounting Customizations""",

    'description': """
    - Analytic Account Branch Distribution.
    - Reuired Analytic Distribution for P&L Accounts.
    - Add Partner for Landed Cost Lines.
    - Partner Ledger Excel.
    - Assets sum for amounts.
    - Add analytic tag for the journal items.
    - Add budget group fot the COA.
    - Budget per branch.
    - Budget Dashboard.
    - Approvals Custom.
    """,
    'author': "Hadeel Ali - ArchDeco",
    'license':'OPL-1',	
    'category': 'Accounts',
    'version': '0.1',
    'depends': ['base', 'analytic', 'branch', 'stock_landed_costs', 'report_xlsx', 'approvals', 'project_status_ubr_dashboard'],

    'data': [
        'security/ir.model.access.csv',
        'security/security_view.xml',

        'data/sequence.xml',

        'views/account_analytic.xml',
        'views/account_move.xml',
        'views/landed_cost.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'views/account_asset.xml',
        'views/account_account.xml',
        'views/account_budget.xml',
        'views/account_payment.xml',
        'views/approvals.xml',
        'views/res_branch.xml',

        'wizards/partner_ledger.xml',

        'reports/partner_ledger.xml',
        'reports/budget_dashboard.xml',

    ],

    'assets': {
        'web.assets_backend': [
            'accounting_customs/static/src/**/*',
        ],
    },
    
    
}
