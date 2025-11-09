# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time, timedelta
import io
import base64



class MonthSalaryBankReportWizard(models.TransientModel):
    _name = "gosi.bank.report.wizard"

    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    company_id = fields.Many2one('employee.company', string='Company')

    def action_excel_wizard(self):
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'company_id': self.company_id.id if self.company_id else False,
        }
        return self.env.ref('gs_hr_payroll_report.action_gosi_bank_salary_xlsx_report').report_action(self, data=data)


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
    _name = 'report.gs_hr_payroll_report.gosi_bank_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        sheet = workbook.add_worksheet('Salary Bank Report')

        # Styles
        title = workbook.add_format({
            'bold': True, 'align': 'center', 'font_size': 20,
            'color': '#FFFFFF', 'bg_color': '#4F81BD', 'border': True
        })
        date_style = workbook.add_format({
            'bold': True, 'align': 'center', 'font_size': 14,
            'border': True
        })
        date_style2 = workbook.add_format({'align': 'center', 'font_size': 12})
        header_row_style = workbook.add_format({
            'bg_color': '#4F81BD', 'color': '#FFFFFF',
            'bold': True, 'align': 'center', 'border': True
        })

        # Title and date range
        sheet.merge_range('A1:K2', 'Month Salary Bank Report', title)
        sheet.merge_range('A4:D4', 'From', date_style)
        sheet.merge_range('A5:D5', data.get('date_from') or '', date_style2)
        sheet.merge_range('E4:H4', 'To', date_style)
        sheet.merge_range('E5:H5', data.get('date_to') or '', date_style2)

        # Set column widths
        for col in range(14):
            sheet.set_column(col, col, 30)

        # Headers
        headers = [
            'كود البنك', 'رقم الحساب البنكي', 'الراتب المستحق', 'رقم وظيفي', 'أسم الموظف', 'رقم الهوية',
            'المشروع', 'الراتب الأساسي', 'بدل السكن', 'بدلات أخري', 'اجمالي الخصومات'
        ]
        for idx, header in enumerate(headers):
            sheet.write(6, idx, header, header_row_style)

        # Domain filters
        domains = []
        if data.get('date_from') and data.get('date_to'):
            domains.append(('date_from', '>=', data.get('date_from')))
            domains.append(('date_to', '<=', data.get('date_to')))

        # Apply company filter only if company_id is provided
        if data.get('company_id'):
            domains.append(('employee_id.employee_company', '=', data.get('company_id')))

        payslips = self.env['hr.payslip'].search(domains)
        row = 7

        for slip in payslips:
            total_basic = 0
            total_house = 0
            total_other_allowance = 0
            total_deductions = 0
            net_salary = 0
            deduct = 0
            for line in slip.line_ids:
                if line.code in ['BASIC', 'الراتب الاساسي']:
                    total_basic += line.total
                elif line.name in ['Housing Allowance', 'بدل السكن']:
                    total_house += line.total
                elif line.name in ['Other Allowances', 'البدلات الاخري', 'Food Allowance',
                                   'Transportation Allowance', 'Others Allowance']:
                    total_other_allowance += line.total
                elif line.name in ['GOSI', 'Loan', 'Absence', 'اجمالى الخصم']:
                    total_deductions += line.total
                elif line.name in ['صافي المرتب', 'Net Salary']:
                    net_salary += line.total


            wage = slip.contract_id.gosi_wage
            allowance = slip.contract_id.gosi_allowance
            house = slip.contract_id.gosi_housing
            if net_salary < wage+allowance+house:
                deduct = net_salary - (wage+allowance+house)
            else:
                deduct = 0
                allowance = net_salary - wage - house


            sheet.write(row, 0, slip.employee_id.bank_account_id.bank_id.bic or "", date_style2)
            sheet.write(row, 1, slip.employee_id.bank_account_id.acc_number or "", date_style2)
            sheet.write(row, 2, net_salary, date_style2)
            sheet.write(row, 3, slip.employee_id.registration_number2 or "", date_style2)
            sheet.write(row, 4, slip.employee_id.name or "", date_style2)
            sheet.write(row, 5, slip.employee_id.identification_id or "", date_style2)
            sheet.write(row, 6, slip.payslip_run_id.name or "", date_style2)
            sheet.write(row, 7, slip.contract_id.gosi_wage, date_style2)
            sheet.write(row, 8, slip.contract_id.gosi_housing, date_style2)
            sheet.write(row, 9, allowance, date_style2)
            # sheet.write(row, 10, total_deductions, date_style2)
            sheet.write(row, 10, deduct, date_style2)

            row += 1
