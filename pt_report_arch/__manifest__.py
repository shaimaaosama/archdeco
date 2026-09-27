{
    "name": "HR Payment Text File Wizard",
    "version": "18.0.1.0.0",
    "depends": ["hr","pt_hr_contract_allowance","hr_payroll","hr_work_entry"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_payment_text_wizard_views.xml",
        "views/payment_company_view.xml",

    ],
    "installable": True,
    "application": False,
}