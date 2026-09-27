# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class installment_line(models.Model):
    _name = 'installment.line'
    _description = 'Lines of an Installment'
    _order = 'date,name'
    
    name = fields.Char('Name')
    employee_id = fields.Many2one('hr.employee',string='Employee')
    loan_id = fields.Many2one('employee.loan',string='Loan',required=True, ondelete='cascade')
    date = fields.Date('Date')
    is_paid = fields.Boolean('Paid')
    amount = fields.Float('Loan Amount')
    interest = fields.Float('Total Interest')
    ins_interest = fields.Float('Interest')
    installment_amt = fields.Float('Installment Amt')
    total_installment = fields.Float('Total',compute='get_total_installment')
    payslip_id = fields.Many2one('hr.payslip',string='Payslip')
    is_skip = fields.Boolean('Skip Installment')
    is_modify = fields.Boolean('Modified')
    payroll_paid = fields.Boolean(default=True,readonly=False)

    # /////////////////////////////////////////////
    journal_entry_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)

    def action_view_journal_entry(self):
        if not self.journal_entry_id:
            raise ValidationError(_("No journal entry linked to this installment."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entry'),
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.journal_entry_id.id,
            'target': 'current',
        }

    # ///////////////////////////////////////
    @api.depends('installment_amt','ins_interest')
    def get_total_installment(self):
        for line in self:
            line.total_installment = line.ins_interest + line.installment_amt
            
            
        
    def action_view_payslip(self):
        if self.payslip_id:
            return {
                'view_mode': 'form',
                'res_id': self.payslip_id.id,
                'res_model': 'hr.payslip',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
                
            }

    def write(self, vals):
        res = super().write(vals)
        self.update_loan_report_state()
        return res

    def update_loan_report_state(self):
        self.loan_id.lone_report_state()

    @api.model
    def update_employee_ids_from_loan(self):
        lines = self.search([('loan_id', '!=', False)])
        for line in lines:
            if line.loan_id.employee_id and line.employee_id != line.loan_id.employee_id:
                line.employee_id = line.loan_id.employee_id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


    @api.model
    def fix_duplicate_names(self):
        loans = self.env['employee.loan'].search([])
        for loan in loans:
            base_name = f'INS - {loan.name} - '
            used_names = set()
            suffix = 1

            # Sort lines by date to preserve order
            for line in loan.installment_lines.sorted('date'):
                # If already unique, keep as is
                if line.name in used_names:
                    # Generate a new unique name
                    while f'{base_name}{suffix}' in used_names:
                        suffix += 1
                    new_name = f'{base_name}{suffix}'
                    line.name = new_name
                    used_names.add(new_name)
                else:
                    used_names.add(line.name)
