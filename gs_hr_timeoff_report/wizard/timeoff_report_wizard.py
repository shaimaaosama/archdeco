# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time, timedelta
import io
import base64


class TimeoffReportWizard(models.TransientModel):
    _name = "timeoff.report.wizard"

    date_from = fields.Date(string="From", )
    date_to = fields.Date(string="To", )
    employee_ids = fields.Many2many('hr.employee')
    timeoff_ids = fields.Many2many('hr.leave.type')

    def action_excel_wizard(self):
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'employee_ids': self.employee_ids.ids,
            'timeoff_ids': self.timeoff_ids.ids,
        }
        return self.env.ref('gs_hr_timeoff_report.action_timeoff_xlsx_report').report_action(self, data=data)


class PreparationFileXlsxReport(models.AbstractModel):
    _name = 'report.gs_hr_timeoff_report.timeoff_xlsx_report'
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
        sheet.merge_range('A1:G2', 'Time Off Report', title)
        money = workbook.add_format({'num_format': '$#,##0.00', 'bg_color': '#ffffff'})
        sheet.merge_range('A4:D4', 'From', date_style)
        sheet.merge_range('A5:D5', data.get('date_from'), date_style2)
        sheet.merge_range('E4:G4', 'To', date_style)
        sheet.merge_range('E5:G5', data.get('date_to'), date_style2)

        # Header row
        sheet.set_column(0, 0, 40)
        sheet.set_column(1, 1, 40)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 4, 40)
        sheet.set_column(5, 5, 40)
        sheet.set_column(6, 6, 40)

        sheet.write(6, 0, 'Name', header_row_style)
        sheet.write(6, 1, 'Business Unit', header_row_style)
        sheet.write(6, 2, 'Timeoff Type', header_row_style)
        sheet.write(6, 3, 'Opening Balance', header_row_style)
        sheet.write(6, 4, 'Allocated During Period', header_row_style)
        sheet.write(6, 5, 'Vacation During Period', header_row_style)
        sheet.write(6, 6, 'Days Balance', header_row_style)

        employees = self.env['hr.employee'].search([])
        timeoff_types = self.env['hr.leave.type'].search([])

        row = 7
        domains = []
        if data.get('date_from') and data.get('date_to'):
            domains.append(('date_from', '>=', data.get('date_from')))
            # domains.append(('date_to', '<=', data.get('date_to')))
        if data.get('employee_ids'):
            employee_ids = data.get('employee_ids')
            domains.append(('employee_id', 'in', employee_ids))
        if data.get('timeoff_ids'):
            timeoff_ids = data.get('timeoff_ids')
            domains.append(('holiday_status_id', 'in', timeoff_ids))

        hr_leave_allocation = self.env['hr.leave.allocation'].search(domains)

        for leave_all in hr_leave_allocation:
            sheet.write(row, 0, leave_all.employee_id.name or "", date_style2)
            sheet.write(row, 1, leave_all.employee_id.branch_id.name or "", date_style2)
            sheet.write(row, 2, leave_all.holiday_status_id.name or "", date_style2)

            domains1 = []
            if data.get('date_from'):
                domains1.append(('date_from', '>=', data.get('date_from')))
            domains1.append(('employee_id', '=', leave_all.employee_id.id))
            domains1.append(('state', '=', 'validate'))
            domains1.append(('holiday_status_id', '=', leave_all.holiday_status_id.id))

            # ال a دي فترة ال allocated بتتحط زي ماهي

            leave_allocation = self.env['hr.leave.allocation'].search(domains1)
            a = 0
            for all in leave_allocation:
                a = all.number_of_days_display
                sheet.write(row, 4, a or 0, date_style2)

            domains00 = []
            if data.get('date_from'):
                domains00.append(('date_from', '<', data.get('date_from')))
            domains00.append(('employee_id', '=', leave_all.employee_id.id))
            domains00.append(('state', '=', 'validate'))
            domains00.append(('holiday_status_id', '=', leave_all.holiday_status_id.id))

            leave_allocation2 = self.env['hr.leave.allocation'].search(domains00)
            x = 0

            # دي اللي بتاخدها علشان تطرح منها الأجازات

            for all2 in leave_allocation2:
                x += all2.number_of_days_display

            domains01 = []
            if data.get('date_from'):
                domains01.append(('date_from', '<', data.get('date_from')))
            domains01.append(('employee_id', '=', leave_all.employee_id.id))
            domains01.append(('holiday_status_id', '=', leave_all.holiday_status_id.id))
            domains01.append(('state', '=', 'validate'))

            hr_leave3 = self.env['hr.leave'].search(domains01)
            y = 0

            # ال y دي الإجازات ما قبل التاريخ في ال timeoff
            for leave3 in hr_leave3:
                y += leave3.number_of_days_display

            opening_balance = x - y
            sheet.write(row, 3, opening_balance or 0, date_style2)

            domains2 = []
            if data.get('date_from') and data.get('date_to'):
                domains2.append(('date_from', '>=', data.get('date_from')))
                # domains2.append(('date_to', '<=', data.get('date_to')))
            domains2.append(('employee_id', '=', leave_all.employee_id.id))
            domains2.append(('state', '=', 'validate'))
            domains2.append(('holiday_status_id', '=', leave_all.holiday_status_id.id))

            # ال a دي فترة ال allocated بتتحط زي ماهي
            leave_allocation = self.env['hr.leave.allocation'].search(domains2)
            allocated_during_period = 0
            for all in leave_allocation:
                allocated_during_period += all.number_of_days_display
            sheet.write(row, 4, allocated_during_period or 0, date_style2)

            domains3 = []
            if data.get('date_from') and data.get('date_to'):
                domains3.append(('date_from', '>=', data.get('date_from')))
                domains3.append(('date_to', '<=', data.get('date_to')))
            domains3.append(('employee_id', '=', leave_all.employee_id.id))
            domains3.append(('holiday_status_id', '=', leave_all.holiday_status_id.id))
            domains3.append(('state', '=', 'validate'))

            hr_leave2 = self.env['hr.leave'].search(domains3)
            vacation_during_period = 0

            # ال b دي الإجازات خلال التاريخ في ال timeoff
            for leave2 in hr_leave2:
                vacation_during_period += leave2.number_of_days_display

            z = x - y
            sum = allocated_during_period + z - vacation_during_period
            sheet.write(row, 3, z or 0, date_style2)
            sheet.write(row, 5, vacation_during_period or 0, date_style2)
            sheet.write(row, 6, sum, date_style2)
            row += 1


            # بداية الأجازات الخاصة بدون أجر المأخوذة من hr leave فقط

        row2 = 0
        domains4 = []
        if data.get('date_from') and data.get('date_to'):
            domains.append(('date_from', '>=', data.get('date_from')))
            domains.append(('date_to', '<=', data.get('date_to')))
        if data.get('employee_ids'):
            employee_ids = data.get('employee_ids')
            domains.append(('employee_id', 'in', employee_ids))
        if data.get('timeoff_ids'):
            timeoff_ids = data.get('timeoff_ids')
            domains.append(('holiday_status_id', 'in', timeoff_ids))

        hr_leave_timeoff = self.env['hr.leave'].search(domains4)

        for leave_all_timeoff in hr_leave_timeoff:
            domains5 = []
            if data.get('date_from'):
                domains5.append(('date_from', '>=', data.get('date_from')))
                domains.append(('date_to', '<=', data.get('date_to')))

            domains5.append(('employee_id', '=', leave_all_timeoff.employee_id.id))
            domains5.append(('state', '=', 'validate'))
            domains5.append(('holiday_status_id', '=', 'إجازة خاصه (بدون أجر)'))

            leave_timeoff = self.env['hr.leave'].search(domains5)
            vacation_during_period_timeoff = 0
            for all_timeoff in leave_timeoff:
                sheet.write(row, 0, all_timeoff.employee_id.name or "", date_style2)
                sheet.write(row, 1, all_timeoff.employee_id.branch_id.name or "", date_style2)
                sheet.write(row, 2, all_timeoff.holiday_status_id.name or "", date_style2)

                vacation_during_period_timeoff += all_timeoff.number_of_days_display
                sheet.write(row, 5, vacation_during_period_timeoff or 0, date_style2)
                sheet.write(row, 6, 0, date_style2)

                row2 += 1
