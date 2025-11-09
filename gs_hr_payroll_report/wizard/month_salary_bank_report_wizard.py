# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time, timedelta
import io
import base64


class MonthSalaryBankReportWizard(models.TransientModel):
    _name = "month.salary.bank.report.wizard"

    date_from = fields.Date(string="From", )
    date_to = fields.Date(string="To", )
    company_id = fields.Many2one('employee.company', string='Company')

    def action_excel_bank_wizard(self):
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'company_id': self.company_id.id if self.company_id else False,
            # 'allowance_ids': self.allowance_ids

        }
        return self.env.ref('gs_hr_payroll_report.action_month_bank_salary_xlsx_report').report_action(self, data=data)



def create_notification(self):
        return {
            'type': 'ir.action.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Warning!'),
                'message': 'Record Empty',
                'sticky': True
            }

        }



class PreparationFileXlsxReport(models.AbstractModel):
    _name = 'report.gs_hr_payroll_report.month_salary_bank_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        sheet = workbook.add_worksheet('')
        bold = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': 'transparent', 'border': True})
        title = workbook.add_format(
            {'bold': True, 'align': 'center', 'font_size': 20,'bg_color': 'transparent', 'color': '#FFFFFF', 'border': True})
        date_style = workbook.add_format(
            {'bold': True, 'align': 'center', 'font_size': 14, 'bg_color': 'transparent', 'border': True})
        date_style2 = workbook.add_format({'align': 'center', 'font_size': 12})

        # Header row style with blue background color
        header_row_style = workbook.add_format(
            {'bg_color': 'transparent', 'color': '#FFFFFF', 'bold': True, 'align': 'center', 'border': True})

        sheet.merge_range('A1:G2', 'Month Salary Bank Report', title)
        money = workbook.add_format({'num_format': '$#,##0.00', 'bg_color': 'transparent'})
        sheet.merge_range('A4:D4', 'From', date_style)
        sheet.merge_range('A5:D5', data.get('date_from'), date_style2)
        sheet.merge_range('E4:G4', 'To', date_style)
        sheet.merge_range('E5:G5', data.get('date_to'), date_style2)

        # Header row
        sheet.set_column(0, 0, 30)
        sheet.set_column(1, 1, 30)
        sheet.set_column(2, 2, 50)
        sheet.set_column(3, 3, 30)
        sheet.set_column(4, 4, 30)
        sheet.set_column(5, 5, 30)
        sheet.set_column(6, 6, 30)
        sheet.set_column(7, 7, 30)
        sheet.set_column(8, 8, 30)
        sheet.set_column(9, 9, 30)
        sheet.set_column(10, 10, 30)
        sheet.set_column(11, 11, 30)
        sheet.set_column(12, 12, 30)
        sheet.set_column(13, 13, 30)


        sheet.write(6, 0, 'كود البنك', header_row_style)
        sheet.write(6, 1, 'رقم الحساب البنكي', header_row_style)
        sheet.write(6, 2, ' الراتب المستحق', header_row_style)
        sheet.write(6, 3, 'رقم وظيفي', header_row_style)
        sheet.write(6, 4, 'أسم الموظف', header_row_style)
        sheet.write(6, 5, 'رقم الهوية', header_row_style)
        sheet.write(6, 6, 'المشروع', header_row_style)
        sheet.write(6, 7, 'الراتب الأساسي', header_row_style)
        sheet.write(6, 8, 'بدل السكن', header_row_style)
        sheet.write(6, 9, 'بدلات أخري', header_row_style)
        sheet.write(6, 10, 'اجمالي الخصومات', header_row_style)



        domains = []
        if data.get('date_from') and data.get('date_to'):
            domains.append(('date_from', '>=', data.get('date_from')))
            domains.append(('date_to', '<=', data.get('date_to')))
        # Apply company filter only if company_id is provided
        if data.get('company_id'):
            domains.append(('employee_id.employee_company', '=', data.get('company_id')))
        else:
            create_notification(self)

        preparation_file_multi = self.env['hr.payslip'].search(domains)
        row = 7
        i = 1
        total_basic = 0
        total_house = 0
        total_transport = 0
        total_other_allowance = 0
        total_award = 0
        total_deduction = 0
        total_dedu=0
        total_gross_salary = 0
        total_loan_deduction = 0
        total_net_salary = 0
        total_combined_deductions = 0
        for pre in preparation_file_multi:
            sheet.write(row, 0, pre.employee_id.bank_account_id.bank_id.bic or "", date_style2)
            sheet.write(row, 1, pre.employee_id.bank_account_id.acc_number or "", date_style2)
            sheet.write(row, 3, pre.employee_id.registration_number2 or "", date_style2)
            sheet.write(row, 4, pre.employee_id.name or "", date_style2)
            sheet.write(row, 5, pre.employee_id.identification_id or "", date_style2)
            sheet.write(row, 6, pre.payslip_run_id.name or "", date_style2)

            gross_salary = 0
            net_salary = 0
            combined_deductions = 0
            combined_other_allowance = 0
            total_other_allowance = 0
            total_deductions = 0  # Initialize total deductions

            for line in pre.line_ids:
                if line.code == 'BASIC' or line.code == 'الراتب الاساسي':
                    sheet.write(row, 7, line.total, date_style2)
                    total_basic += line.total
                if line.name in ['Housing Allowance', 'بدل السكن']:
                    sheet.write(row, 8, line.total, date_style2)
                    combined_other_allowance += line.total
                if line.name in ['Other Allowances', 'البدلات الاخري', 'Food Allowance', 'Transportation Allowance','Others Allowance']:
                    combined_other_allowance += line.total
                    total_other_allowance += line.total
                if line.name in ['صافي المرتب', 'Net Salary']:
                    sheet.write(row, 2, line.total, date_style2)
                    total_net_salary += line.total
                if line.name in ['GOSI', 'Loan', 'Absence', 'اجمالى الخصم']:  # Sum deductions
                    total_deductions += line.total

            # Write the final accumulated values after looping
            sheet.write(row, 9, total_other_allowance, date_style2)  # Other Allowance Total
            sheet.write(row, 10, total_deductions, date_style2)  # Total Deductions

            # sheet.write(row, 10, combined_deductions, date_style2)  # Updated column index
            # total_combined_deductions += combined_deductions
            # sheet.write(row, 9, combined_other_allowance, date_style2)
            # total_other_allowance += combined_other_allowance
            row += 1


        # Writing the totals
        # sheet.write(row, 7, total_basic, date_style2)
        # sheet.write(row, 8, total_house, date_style2)
        # sheet.write(row, 9, total_other_allowance, date_style2)  # Updated column index
        # sheet.write(row, 5, total_gross_salary, date_style2)
        # sheet.write(row, 10, total_combined_deductions, date_style2)  # Updated column index
        # sheet.write(row, 6, total_net_salary, date_style2)
        # sheet.write(row, 11, total_dedu, date_style2)


        for wizard in self:
            fp = io.BytesIO()
            workbook.save(fp)
            excel_file = base64.encodestring(fp.getvalue())
            wizard.leave_summary_file = excel_file
            wizard.file_name = 'Month Salary Bank Report.xls'
            wizard.leave_report_printed = True
            fp.close()
            return {
                'view_mode': 'form',
                'res_id': wizard.id,
                'res_model': 'month.salary.bank.report.wizard',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
                'context': self.env.context,
                'target': 'new',
            }
