# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

{
    "name": "Contacts Approval",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "version": "15.0.1",
    "license": "OPL-1",
    "category": "Human Resources",
    "summary": """
Contact Approval Odoo, Vendor Approval, Partner Management. 
Contact Manager Approve contacts, 
Partner Rejection By Contact Manager, Mass Vendor Approve, 
Multiple Supplier Approve, Bulk Client Reject, 
All User Reject In Single Click Odoo""",

    "description": """
The contact approval module will allow you to approve or reject contacts,
partners, vendors, customers, clients only by-Contact manager,
Only approved contacts, partners, vendors, customers,
clients can be used in Sale, Purchase, Invoices, CRM & Inventory, etc.
When Contact create that will put it in the "Under Approval" state by default
and then after contact manager can move in approve or not approve state.
The approved contact will appear in the whole odoo.
This module gives the facility to the contact manager to select multiple
contacts means mass approval or mass reject contacts.
Contact Approval Odoo, Vendor Approval, Partner Management Odoo
Contact Manager Approve Contacts Module, Partner Rejection By Contact Manager,
Mass Vendor Approve, Multiple Supplier Approve In Single Click,
Bulk Client Reject, All User Reject In Single Click Odoo.
Contact Manager Approve contacts Module, Partner Rejection By Contact Manager,
Mass Vendor Approve, Multiple Supplier Approve In Single Click,
Bulk Client Reject, All User Reject In Single Click Odoo.
""",
    "depends": [
        "contacts",
        "sale_management",
        "account",
        "purchase",
        "stock"
    ],
    "data": [
        "security/sh_mass_approve_contact_security.xml",
        "views/contact_view.xml",
    ],
    "images": ["static/description/background.png"],
    "live_test_url": "https://youtu.be/auIwqrHtDiw",
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": 25,
    "currency": "EUR"
}
