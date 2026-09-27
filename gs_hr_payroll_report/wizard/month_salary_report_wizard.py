# # -*- coding: utf-8 -*-
#
# from odoo import models, fields, api, _
# from odoo.exceptions import AccessError, UserError, ValidationError
# from dateutil.relativedelta import relativedelta
# from datetime import date, datetime, time, timedelta
# import io
# import base64
#
#
# class MonthSalaryReportWizard(models.TransientModel):
#     _name = "month.salary.report.wizard"
#
#
#     date_from = fields.Date(string="From", )
#     date_to = fields.Date(string="To", )
#     company_id = fields.Many2one('res.company' , string='Company')
#
#     # allowance_ids = fields.Many2many('hr.allowance')
#
#     def action_excel_wizard(self):
#         data = {
#             'date_from': self.date_from,
#             'date_to': self.date_to,
#             'company_id': self.company_id.id if self.company_id else False,
#             # 'allowance_ids': self.allowance_ids
#
#         }
#         return self.env.ref('gs_hr_payroll_report.action_month_salary_xlsx_report').report_action(self, data=data)
#
#
# def create_notification(self):
#     return {
#         'type': 'ir.action.client',
#         'tag': 'display_notification',
#         'params': {
#             'title': _('Warning!'),
#             'message': 'Record Empty',
#             'sticky': True
#         }
#
#     }
#
#
# class PreparationFileXlsxReport(models.AbstractModel):
#     _name = 'report.gs_hr_payroll_report.month_salary_xlsx_report'
#     _inherit = 'report.report_xlsx.abstract'
#
#     def generate_xlsx_report(self, workbook, data, partners):
#         sheet = workbook.add_worksheet('')
#         bold = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#fffbed', 'border': True})
#         title = workbook.add_format(
#             {'bold': True, 'align': 'center', 'font_size': 20, 'bg_color': '#f2f2f2', 'border': True})
#         date_style = workbook.add_format(
#             {'bold': True, 'align': 'center', 'font_size': 14, 'bg_color': '#f2f2f2', 'border': True})
#         date_style2 = workbook.add_format({'align': 'center', 'font_size': 12})
#         header_row_style = workbook.add_format(
#             {'bg_color': '#f2f2f2', 'color': '#000000', 'bold': True, 'align': 'center', 'border': True})
#         sheet.merge_range('A1:G2', 'Month Salary Report', title)
#         money = workbook.add_format({'num_format': '$#,##0.00', 'bg_color': '#ffffff'})
#         sheet.merge_range('A4:D4', 'From', date_style)
#         sheet.merge_range('A5:D5', data.get('date_from'), date_style2)
#         sheet.merge_range('E4:G4', 'To', date_style)
#         sheet.merge_range('E5:G5', data.get('date_to'), date_style2)
#
#         # Header row
#         sheet.set_column(0, 0, 5)
#         sheet.set_column(1, 1, 20)
#         sheet.set_column(2, 2, 50)
#         sheet.set_column(3, 3, 30)
#         sheet.set_column(4, 4, 30)
#         sheet.set_column(5, 5, 30)
#         sheet.set_column(6, 6, 30)
#         sheet.set_column(7, 7, 30)
#         sheet.set_column(8, 8, 30)
#         sheet.set_column(9, 9, 30)
#         sheet.set_column(10, 10, 30)
#         sheet.set_column(11, 11, 30)
#         sheet.set_column(12, 12, 30)
#         sheet.set_column(13, 13, 30)
#         sheet.set_column(14, 14, 30)
#         sheet.set_column(15, 15, 30)
#         sheet.set_column(16, 16, 30)
#         sheet.set_column(16, 17, 30)
#         sheet.set_column(16, 18, 30)
#         sheet.set_column(16, 19, 30)
#         sheet.set_column(16, 20, 30)
#         sheet.set_column(16, 21, 30)
#         sheet.set_column(16, 22, 30)
#         sheet.set_column(16, 23, 30)
#         sheet.set_column(16, 24, 30)
#         sheet.set_column(16, 25, 30)
#         sheet.set_column(16, 26, 30)
#         sheet.set_column(16, 27, 30)
#         sheet.set_column(16, 28, 30)
#         sheet.set_column(16, 29, 30)
#         sheet.set_column(16, 30, 30)
#         sheet.set_column(16, 31, 30)
#         sheet.set_column(16, 32, 30)
#         sheet.set_column(16, 33, 30)
#         sheet.set_column(16, 34, 30)
#         sheet.set_column(16, 35, 30)
#         sheet.set_column(16, 36, 30)
#         sheet.set_column(16, 37, 30)
#
#         # Static headers
#         static_headers = [
#             'رقم', 'رقم الموظف', 'اي دي', 'أسم الموظف', 'أسم الدفعة', 'من', 'إلي',
#             'رقم الحساب البنكي', 'أسم البنك'
#         ]
#
#         # Write static headers in row 6
#         for col, header in enumerate(static_headers):
#             sheet.write(6, col, header, header_row_style)
#
#         domains = []
#         if data.get('date_from') and data.get('date_to'):
#             domains.append(('date_from', '>=', data.get('date_from')))
#             domains.append(('date_to', '<=', data.get('date_to')))
#         if data.get('company_id'):
#             domains.append(('employee_id.company_id', '=', data.get('company_id')))
#         else:
#             create_notification(self)
#
#         preparation_file_multi = self.env['hr.payslip'].search(domains)
#         # Gather unique line names dynamically
#         unique_line_names = set()
#         for pre in preparation_file_multi:
#             for line in pre.line_ids:
#                 unique_line_names.add(line.name)
#
#         # Sort line names for consistent column order
#         sorted_line_names = sorted(unique_line_names)
#
#         # Write dynamic headers for line names
#         start_col = len(static_headers)
#         for col, line_name in enumerate(sorted_line_names, start=start_col):
#             sheet.write(6, col, line_name, header_row_style)
#
#         # Write data rows
#         row = 7
#         i = 1
#         for pre in preparation_file_multi:
#             # Write static data
#             sheet.write(row, 0, i, date_style2)
#             sheet.write(row, 1, pre.employee_id.registration_number2 or "", date_style2)
#             sheet.write(row, 2, pre.employee_id.identification_id or "", date_style2)
#             sheet.write(row, 3, pre.employee_id.name or "", date_style2)
#             sheet.write(row, 4, pre.payslip_run_id.name or "", date_style2)
#             sheet.write(row, 5, pre.date_from.strftime('%Y-%m-%d') or "", date_style2)
#             sheet.write(row, 6, pre.date_to.strftime('%Y-%m-%d') or "", date_style2)
#             sheet.write(row, 7, pre.employee_id.bank_account_id.acc_number or "", date_style2)
#             sheet.write(row, 8, pre.employee_id.bank_account_id.bank_id.bic or "", date_style2)
#
#             # Write dynamic line values
#             col = start_col
#             for line_name in sorted_line_names:
#                 # Find the line with this name
#                 line = next((l for l in pre.line_ids if l.name == line_name), None)
#                 sheet.write(row, col, line.total if line else 0, date_style2)
#                 col += 1
#
#             row += 1
#             i += 1
#
#
#         for wizard in self:
#             fp = io.BytesIO()
#             workbook.save(fp)
#             excel_file = base64.encodestring(fp.getvalue())
#             wizard.leave_summary_file = excel_file
#             wizard.file_name = 'Month Salary Report.xls'
#             wizard.leave_report_printed = True
#             fp.close()
#             return {
#                 'view_mode': 'form',
#                 'res_id': wizard.id,
#                 'res_model': 'month.salary.report.wizard',
#                 'view_type': 'form',
#                 'type': 'ir.actions.act_window',
#                 'context': self.env.context,
#                 'target': 'new',
#             }

# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time, timedelta
import io
import base64

class NewCompany(models.Model):
    _name = 'employee.company'

    name = fields.Char()


class HrEmp(models.Model):
    _inherit = 'hr.employee'

    employee_company = fields.Many2one('employee.company' , string='Employee Company')


class MonthSalaryReportWizard(models.TransientModel):
    _name = "month.salary.report.wizard"

    date_from = fields.Date(string="From", )
    date_to = fields.Date(string="To", )
    company_id = fields.Many2one('res.company', string='Company')

    # allowance_ids = fields.Many2many('hr.allowance')

    def action_excel_bank_wizard(self):
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'company_id': self.company_id.id if self.company_id else False,
            # 'allowance_ids': self.allowance_ids

        }
        return self.env.ref('gs_hr_payroll_report.action_month_salary_xlsx_report').report_action(self, data=data)
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
    _name = 'report.gs_hr_payroll_report.month_salary_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        sheet = workbook.add_worksheet('')
        bold = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#fffbed', 'border': True})
        title = workbook.add_format(
            {'bold': True, 'align': 'center', 'font_size': 20, 'bg_color': '#f2f2f2', 'border': True})
        date_style = workbook.add_format(
            {'bold': True, 'align': 'center', 'font_size': 14, 'bg_color': '#f2f2f2', 'border': True})
        date_style2 = workbook.add_format({'align': 'center', 'font_size': 12})
        header_row_style = workbook.add_format(
            {'bg_color': '#f2f2f2', 'color': '#000000', 'bold': True, 'align': 'center', 'border': True})
        sheet.merge_range('A1:G2', 'Month Salary Report', title)
        money = workbook.add_format({'num_format': '$#,##0.00', 'bg_color': '#ffffff'})
        sheet.merge_range('A4:D4', 'From', date_style)
        sheet.merge_range('A5:D5', data.get('date_from'), date_style2)
        sheet.merge_range('E4:G4', 'To', date_style)
        sheet.merge_range('E5:G5', data.get('date_to'), date_style2)

        # Header row
        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 20)
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
        sheet.set_column(14, 14, 30)
        sheet.set_column(15, 15, 30)
        sheet.set_column(16, 16, 30)
        sheet.set_column(16, 17, 30)
        sheet.set_column(16, 18, 30)
        sheet.set_column(16, 19, 30)
        sheet.set_column(16, 20, 30)
        sheet.set_column(16, 21, 30)
        sheet.set_column(16, 22, 30)
        sheet.set_column(16, 23, 30)
        sheet.set_column(16, 24, 30)
        sheet.set_column(16, 25, 30)
        sheet.set_column(16, 26, 30)
        sheet.set_column(16, 27, 30)
        sheet.set_column(16, 28, 30)
        sheet.set_column(16, 29, 30)
        sheet.set_column(16, 30, 30)
        sheet.set_column(16, 31, 30)
        sheet.set_column(16, 32, 30)
        sheet.set_column(16, 33, 30)
        sheet.set_column(16, 34, 30)
        sheet.set_column(16, 35, 30)
        sheet.set_column(16, 36, 30)
        sheet.set_column(16, 37, 30)

        # Static headers
        static_headers = [
            'رقم', 'رقم الموظف' , 'اي دي', 'أسم الموظف', 'أسم الدفعة', 'من', 'إلي',
            'رقم الحساب البنكي', 'أسم البنك'
        ]

        # Write static headers in row 6
        for col, header in enumerate(static_headers):
            sheet.write(6, col, header, header_row_style)

        domains = []
        if data.get('date_from') and data.get('date_to'):
            domains.append(('date_from', '>=', data.get('date_from')))
            domains.append(('date_to', '<=', data.get('date_to')))

        # Apply company filter only if company_id is provided
        if data.get('company_id'):
            domains.append(('employee_id.employee_company', '=', data.get('company_id')))

        preparation_file_multi = self.env['hr.payslip'].search(domains)
        # Gather unique line names dynamically
        unique_line_names = set()
        for pre in preparation_file_multi:
            for line in pre.line_ids:
                unique_line_names.add(line.name)

        # Sort line names for consistent column order
        sorted_line_names = sorted(unique_line_names)

        # Write dynamic headers for line names
        start_col = len(static_headers)
        for col, line_name in enumerate(sorted_line_names, start=start_col):
            sheet.write(6, col, line_name, header_row_style)

        # Write data rows
        row = 7
        i = 1
        for pre in preparation_file_multi:
            # Write static data
            sheet.write(row, 0, i, date_style2)
            sheet.write(row, 1, pre.employee_id.registration_number2 or "", date_style2)
            sheet.write(row, 2, pre.employee_id.identification_id or "", date_style2)
            sheet.write(row, 3, pre.employee_id.name or "", date_style2)
            sheet.write(row, 4, pre.payslip_run_id.name or "", date_style2)
            sheet.write(row, 5, pre.date_from.strftime('%Y-%m-%d') or "", date_style2)
            sheet.write(row, 6, pre.date_to.strftime('%Y-%m-%d') or "", date_style2)
            sheet.write(row, 7, pre.employee_id.bank_account_id.acc_number or "", date_style2)
            sheet.write(row, 8, pre.employee_id.bank_account_id.bank_id.bic or "", date_style2)

            # Write dynamic line values
            col = start_col
            for line_name in sorted_line_names:
                # Find the line with this name
                line = next((l for l in pre.line_ids if l.name == line_name), None)
                sheet.write(row, col, line.total if line else 0, date_style2)
                col += 1

            row += 1
            i += 1



        for wizard in self:
            fp = io.BytesIO()
            workbook.save(fp)
            excel_file = base64.encodestring(fp.getvalue())
            wizard.leave_summary_file = excel_file
            wizard.file_name = 'Month Salary Report.xls'
            wizard.leave_report_printed = True
            fp.close()
            return {
                'view_mode': 'form',
                'res_id': wizard.id,
                'res_model': 'month.salary.report.wizard',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
                'context': self.env.context,
                'target': 'new',
            }