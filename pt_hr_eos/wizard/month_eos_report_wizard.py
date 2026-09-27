# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, fields, _


class MonthEosReportWizard(models.TransientModel):
    _name = "month.eos.report.wizard"
    _description = "Monthly EOS Report Wizard"

    date_from = fields.Date(string="From", )
    date_to = fields.Date(string="To", )
    eos_year = fields.Selection(
        [(str(year), str(year)) for year in range(2000, 2081)],
        string="Eos Years Report",
        default=str(fields.Date.today().year),
        required=True,
    )
    employee_id = fields.Many2one('hr.employee', domain="[('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    # allowance_ids = fields.Many2many('hr.allowance')

    def action_excel_wizard(self):
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'eos_year': self.eos_year,
            'company_id': self.company_id.id,
            'employee_id': self.employee_id.id,
            # 'allowance_ids': self.allowance_ids

        }
        return self.env.ref('gs_hr_eos.action_month_eos_xlsx_report').report_action(self, data=data)


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
    _name = 'report.gs_hr_eos.month_eos_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Monthly EOS XLSX Report'

    def generate_xlsx_report(self, workbook, data, partners):
        sheet = workbook.add_worksheet('Eos Monthly Report')

        # Define formats
        title_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'font_size': 16, 'bg_color': '#4F81BD', 'color': 'white', 'border': 1})
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#DCE6F1', 'border': 1})
        totals_row_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'bg_color': '#4F81BD', 'color': 'white', 'border': 1,
             'num_format': '#,##0.00'})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd', 'align': 'center', 'border': 1})
        money_format = workbook.add_format({'num_format': '#,##0.00', 'align': 'center', 'border': 1})

        # Write title and year
        sheet.merge_range('A1:L2', 'تقرير نهاية الخدمة السنوي', title_format)  # تم تعديل النطاق ليشمل العمود L
        sheet.merge_range('A4:F4', 'سنة', header_format)
        sheet.merge_range('A5:F5', data.get('eos_year', ''), date_format)
        sheet.set_row(6, 60)
        sheet.set_column('A:O', 40)  # تم تعديل النطاق ليشمل العمود L

        # Headers
        headers = [('Employee Code', 'كود الموظف'), ('Employee Name', 'اسم الموظف'),('Department', 'القسم'),
                   ('Hiring Date', 'تاريخ التعيين'), ('Salary', 'الراتب'),
            ('Cost Center', 'الفرع'), ('Years of Service', 'Years'),('Years of Service', 'Months'),('Years of Service', 'Days'),
            ('Opening Balance', 'الرصيد الافتتاحي'), ('Component Balance', 'الرصيد المكون'),
            ('Final Balance', 'الرصيد النهائي'), ('Salary Until Change', 'الراتب حتى تاريخ التغيير'),
            ('Salary After Change', 'الراتب من تاريخ التغيير'), ('Difference', 'الفرق'),
        ]
        sheet.merge_range(6, 6, 6, 8, "Years of Service", header_format)

        for col, (english, arabic) in enumerate(headers):
            sheet.write(6, col, english, header_format)
            sheet.write(7, col, arabic, header_format)
        sheet.set_row(6, 25)
        sheet.set_row(7, 25)

        # Prepare domains for current and previous year
        eos_year = datetime.strptime(data['eos_year'], '%Y') if data.get('eos_year') else None
        if eos_year:
            year_start = eos_year.replace(month=1, day=1).date()
            year_end = eos_year.replace(month=12, day=31).date()
            domains = [
                ('company_id', '=', int(data.get('company_id'))),
                ('date', '>=', year_start.strftime('%Y-%m-%d')),
                ('date', '<=', year_end.strftime('%Y-%m-%d')),
            ]
            previous_year_domains = [
                ('company_id', '=', int(data.get('company_id'))),
                ('date', '<', year_start.strftime('%Y-%m-%d')),
            ]

        # Fetch data
        preparation_file_multi = self.env['gs.eos.monthly'].search(domains)
        previous_year_data = self.env['gs.eos.monthly'].search(previous_year_domains)

        # Precompute opening balances
        opening_balances = {}
        for prev in previous_year_data:
            emp_id = prev.employee_id.id
            opening_balances[emp_id] = opening_balances.get(emp_id, 0) + (prev.eos_total_amount_month or 0)

        # Aggregate data
        employee_data = {}
        for pre in preparation_file_multi:
            emp_id = pre.employee_id.id
            contract = pre.employee_id.contract_id
            if emp_id not in employee_data:
                employee_data[emp_id] = {
                    'employee': pre.employee_id,
                    'salary': contract.eos_total_amount or 0,  # الراتب الحالي للعرض فقط
                    'change_date': contract.change_date,
                    'opening_balance': opening_balances.get(emp_id, 0),
                    'component_balance': 0,
                    'monthly_records': [],
                }
            employee_data[emp_id]['component_balance'] += pre.eos_total_amount_month or 0
            employee_data[emp_id]['monthly_records'].append(pre)

        def get_years(start_date, end_date):
            if not start_date:
                return "0 0"
            delta = end_date - start_date
            total_days = delta.days
            years = total_days // 365
            remaining_days = total_days % 365
            months = remaining_days // 30
            days = remaining_days % 30
            return years
        def get_months(start_date, end_date):
                if not start_date:
                    return "0 0"
                delta = end_date - start_date
                total_days = delta.days
                years = total_days // 365
                remaining_days = total_days % 365
                months = remaining_days // 30
                days = remaining_days % 30
                return months
        def get_days(start_date, end_date):
                if not start_date:
                    return "0 0"
                delta = end_date - start_date
                total_days = delta.days
                years = total_days // 365
                remaining_days = total_days % 365
                months = remaining_days // 30
                days = remaining_days % 30
                return days

        def calculate_salary_periods(monthly_records, change_date, year_start, year_end):
            salary_until_change = 0
            salary_after_change = 0

            if not change_date or change_date < year_start or change_date > year_end:
                # for record in monthly_records:
                #     salary_after_change += record.eos_total_amount_month or 0
                return salary_until_change, salary_after_change

            for record in monthly_records:
                record_date = record.date
                if record_date < change_date:
                    salary_until_change += record.eos_total_amount_month or 0
                else:
                    salary_after_change += record.eos_total_amount_month or 0

            return salary_until_change, salary_after_change

        # Prepare rows with proper date handling
        rows_data = []
        total_salary = total_opening_balance = total_component_balance = total_salary_until_change = total_salary_after_change = total_difference = 0
        end_date = data.get('date_to') and datetime.strptime(data['date_to'], '%Y-%m-%d') or datetime.now()

        for emp_id, emp_record in employee_data.items():
            emp = emp_record['employee']
            hire_date_str = emp.contract_id.date_hired or ''
            hire_date = hire_date_str and datetime.strptime(str(hire_date_str), '%Y-%m-%d') or None
            years_of_service = get_years(hire_date, end_date) if hire_date else "0 0"
            month_of_service = get_months(hire_date, end_date) if hire_date else "0 0"
            days_of_service = get_days(hire_date, end_date) if hire_date else "0 0"

            birthday_str = emp.birthday or ''
            birthday = birthday_str and datetime.strptime(str(birthday_str), '%Y-%m-%d') or None

            final_balance = emp_record['opening_balance'] + emp_record['component_balance']
            salary_until_change, salary_after_change = calculate_salary_periods(
                emp_record['monthly_records'], emp_record['change_date'], year_start, year_end
            )
            if salary_until_change > salary_after_change:
                difference = salary_until_change - salary_after_change  # حساب الفرق
            elif salary_after_change > salary_until_change:
                difference = salary_after_change - salary_until_change
            else:
                difference = 0


            rows_data.append([
                emp.registration_number2 or '', emp.name or '',emp.department_id.name or '',
                hire_date_str, emp_record['salary'], emp.contract_id.analytic_account_id.name or '',#emp.branch_id.name or
                years_of_service,month_of_service,days_of_service, emp_record['opening_balance'], emp_record['component_balance'],
                final_balance, salary_until_change, salary_after_change, difference
            ])
            total_salary += emp_record['salary']
            total_opening_balance += emp_record['opening_balance']
            total_component_balance += emp_record['component_balance']
            total_salary_until_change += salary_until_change
            total_salary_after_change += salary_after_change
            total_difference += difference

        # Write rows with mixed formats
        for row_idx, row_data in enumerate(rows_data, start=8):
            sheet.write(row_idx, 1, row_data[1], money_format)  # Hiring Date
            sheet.write(row_idx, 4, row_data[4], money_format)  # Date of Birth
            sheet.write(row_idx, 0, row_data[0], money_format)  # Employee Name
            sheet.write(row_idx, 2, row_data[2], money_format)  # Salary
            sheet.write(row_idx, 3, row_data[3], date_format)  # Branch
            sheet.write(row_idx, 5, row_data[5], money_format)  # Years of Service
            # sheet.write(row_idx, 6, row_data[6], money_format)  # Opening Balance
            sheet.write(row_idx, 6, row_data[6], money_format)  # Component Balance
            sheet.write(row_idx, 7, row_data[7], money_format)  # Final Balance
            sheet.write(row_idx, 8, row_data[8], money_format)  # Salary Until Change
            sheet.write(row_idx, 9, row_data[9], money_format)  # Salary After Change
            sheet.write(row_idx, 10, row_data[10], money_format)  # Difference
            sheet.write(row_idx, 11, row_data[11], money_format)  # Difference
            sheet.write(row_idx, 12, row_data[12], money_format)  # Difference
            sheet.write(row_idx, 13, row_data[13], money_format)  # Difference
            sheet.write(row_idx, 14, row_data[14], money_format)  # Difference

        # Write totals
        totals_row = len(rows_data) + 8
        total_final_balance = total_opening_balance + total_component_balance
        sheet.merge_range(totals_row, 0, totals_row, 1, 'الإجمالي', totals_row_format)
        sheet.write(totals_row, 4, total_salary, totals_row_format)
        sheet.write(totals_row, 9, total_opening_balance, totals_row_format)
        sheet.write(totals_row, 10, total_component_balance, totals_row_format)
        sheet.write(totals_row, 11, total_final_balance, totals_row_format)
        sheet.write(totals_row, 12, total_salary_until_change, totals_row_format)
        sheet.write(totals_row, 13, total_salary_after_change, totals_row_format)
        sheet.write(totals_row, 14, total_difference, totals_row_format)

        return