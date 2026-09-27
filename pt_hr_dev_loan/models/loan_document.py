    # -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd. (<http://devintellecs.com>).
#
##############################################################################
from odoo import fields, models, api
from datetime import date

class dev_loan_document(models.Model):
    _name='dev.loan.document'
    _description = 'Document of Loan of Employee'

    sequ_name = fields.Char(string ='Sequence',readonly=True,copy= False)
    name = fields.Char(string = 'Name',required=True)
    employee_id = fields.Many2one('hr.employee',string = 'Employee',required=True)
    loan_id = fields.Many2one('employee.loan',string = 'Loan')
    document = fields.Binary(string ='Document',required=True,copy= False)
    date = fields.Date(string = 'Date', default=date.today())
    note = fields.Text(string ='Note')
    
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['sequ_name'] = self.env['ir.sequence'].next_by_code('dev.loan.document') or 'LOAN/DOC/'
        return super().create(vals_list)
        
    
   
