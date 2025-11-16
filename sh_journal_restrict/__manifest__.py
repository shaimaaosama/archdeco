# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Journal Restriction For Users",
    "author": "Softhealer Technologies",
    "license": "OPL-1",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Accounting",
    "summary": "Journal Security,Journal Restricted Users,Journal Restrictions,Restrict Creation Of Journal,Journal Restriction for User, User access on journal,Journal Restriction Access,Allowed Journal,Account Journal Restriction,Journal Base User Access Odoo",
    "description": """This module restricts journals for specific users. You can add access users on journal configuration, only allowed users can access that journal. Users are allocated in specific journals like invoice, bill, cash, bank, sale & purchase, So users can not access a journal where the journal is not available for that user.""",
    "depends": [
        "account"
    ],
    "application": True,
    "data": [

        "security/sh_journal_restrict_security.xml",
        "views/sh_account.xml",

    ],

    "images": ["static/description/background.png", ],
    "auto_install": False,
    "installable": True,
    "price": "22",
    "currency": "EUR"
}
