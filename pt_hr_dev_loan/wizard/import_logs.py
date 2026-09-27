# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import fields, models


class import_logs(models.TransientModel):
    _name = "import.logs"
    _description = "Import Loan Logs"


    name = fields.Text(string='Logs')
    
    
            

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
    
