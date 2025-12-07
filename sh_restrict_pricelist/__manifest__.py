# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Restrict Pricelist",
    "author" : "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Sales",
    "summary": "Restrict Price list,  Pricelist Security App, Pricelist Allocation Module, User Pricelist, Pricelist Visiblity, restrict pricelist for user Odoo",
    "description": """Currently in odoo users can see all the pricelist with price details. so do you want different restrictions on the pricelist for different users? So here we build a module that can help to display specific pricelist to the user.How did it work? you need to go inside the particular user and select pricelist, which pricelist you want to visible for that user. if you don't give any pricelist than all pricelist will be accessible/visible. supposed you have selected some pricelist than only that selected pricelist will be accessible. wherever the pricelist field of view it will affect to all those fields. Cheers!
 Restrict Pricelist In Odoo.""",
    "version": "15.0.1",
    "depends": [
        'sale_management'
    ],
    "application" : True,
    "data": [
        'views/res_users_inherit_view.xml',
    ],
    "images": ["static/description/background.jpg", ],
    "live_test_url": "https://www.youtube.com/watch?v=hKmKGWSlmQE&feature=youtu.be",
    "license": "OPL-1",
    "auto_install": False,
    "installable" : True,
    "price": 25,
    "currency": "EUR"

}
