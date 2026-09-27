# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import models, fields


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    loan_request = fields.Integer('Loan Request Per Year', default=1, required=True)

class hr_employee_public(models.Model):
    _inherit = 'hr.employee.public'

    loan_request = fields.Integer('Loan Request Per Year', default=1, required=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
