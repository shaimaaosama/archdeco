# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
import calendar


class GsEOS(models.Model):
    _name = 'gs.eos'
    _description = 'End Of Service'

    name = fields.Char(string='Name')
    contract_type = fields.Selection(string='Type of Contract', selection=[('fixed_time', 'Fixed time'),
                                                                           ('unlimited_period', 'Unlimited period'), ],
                                     required=False, )

    reason_id = fields.Many2one('gs.end.reason', string='Reason', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    joining_date = fields.Date(string='Joining Date', related='employee_id.joining_date',
                               help="Employee joining date computed from the contract start date")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    eos_total_amount = fields.Monetary('EOS Total Amount', readonly=True)
    end_of_service = fields.Date(string='End Of Service Date', )
    service_period = fields.Char(string='Service Period')

    year = fields.Integer(string='Year')
    month = fields.Integer(string='Month')
    day = fields.Integer(string='Day')

    value = fields.Float(string='Value')

    @api.onchange('contract_type')
    def domain_reason_id(self):
        for rec in self:
            if rec.contract_type == 'fixed_time':
                return {'domain': {'reason_id': [('contract_type', '=', 'fixed_time')]}}
            elif rec.contract_type == 'unlimited_period':
                return {'domain': {'reason_id': [('contract_type', '=', 'unlimited_period')]}}

    @api.onchange('reason_id', 'year', 'month', 'day')
    def _onchange_reason_id(self):
        for rec in self:
            if rec.contract_type == 'fixed_time':
                if rec.reason_id.id == self.env.ref('gs_hr_eos.gs_end_reason7').id and rec.reason_id.id == self.env.ref(
                        'gs_hr_eos.gs_end_reason3').id:
                    rec.value = 0
                else:
                    if rec.year <= 5:
                        if rec.year == 5 and rec.month > 0 and rec.day > 0:
                            if rec.end_of_service:
                                end_of_service = datetime(rec.end_of_service.year, rec.end_of_service.month,
                                                          calendar.mdays[rec.end_of_service.month])
                                days_end_date = end_of_service.day
                                available_days = 0
                                day_in_months = 0
                                if rec.month > 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = rec.month + day_in_months

                                elif rec.month == 0 and rec.year > 0:
                                    if rec.day > 0:
                                        day_in_months = rec.day / days_end_date
                                    available_days = (rec.year * 12) + day_in_months

                                elif rec.month == 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = round(day_in_months)

                                elif rec.month > 0 and rec.year > 0 and rec.day > 0:
                                    day = rec.day / days_end_date
                                    months = rec.month + day
                                    available_days = (rec.year * 12) + months

                                elif rec.month > 0 and rec.year > 0 and rec.day == 0:
                                    months = rec.month
                                    available_days = (rec.year * 12) + months
                                if available_days > 5:
                                    after_available = available_days - 60
                                    value = (rec.eos_total_amount / 12) * after_available
                                    value2 = (rec.eos_total_amount / 24) * 60
                                    rec.value = value + value2
                        elif rec.year == 5 and rec.month > 0 and rec.day == 0:
                            if rec.end_of_service:
                                end_of_service = datetime(rec.end_of_service.year, rec.end_of_service.month,
                                                          calendar.mdays[rec.end_of_service.month])
                                days_end_date = end_of_service.day
                                available_days = 0
                                day_in_months = 0
                                if rec.month > 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = rec.month + day_in_months

                                elif rec.month == 0 and rec.year > 0:
                                    if rec.day > 0:
                                        day_in_months = rec.day / days_end_date
                                    available_days = (rec.year * 12) + day_in_months

                                elif rec.month == 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = round(day_in_months)

                                elif rec.month > 0 and rec.year > 0 and rec.day > 0:
                                    day = rec.day / days_end_date
                                    months = rec.month + day
                                    available_days = (rec.year * 12) + months

                                elif rec.month > 0 and rec.year > 0 and rec.day == 0:
                                    months = rec.month
                                    available_days = (rec.year * 12) + months
                                if available_days > 5:
                                    after_available = available_days - 60
                                    value = (rec.eos_total_amount / 12) * after_available
                                    value2 = (rec.eos_total_amount / 24) * 60
                                    rec.value = value + value2
                        elif rec.year == 5 and rec.month == 0 and rec.day > 0:
                            if rec.end_of_service:
                                end_of_service = datetime(rec.end_of_service.year, rec.end_of_service.month,
                                                          calendar.mdays[rec.end_of_service.month])
                                days_end_date = end_of_service.day
                                available_days = 0
                                day_in_months = 0
                                if rec.month > 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = rec.month + day_in_months

                                elif rec.month == 0 and rec.year > 0:
                                    if rec.day > 0:
                                        day_in_months = rec.day / days_end_date
                                    available_days = (rec.year * 12) + day_in_months

                                elif rec.month == 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = round(day_in_months)

                                elif rec.month > 0 and rec.year > 0 and rec.day > 0:
                                    day = rec.day / days_end_date
                                    months = rec.month + day
                                    available_days = (rec.year * 12) + months

                                elif rec.month > 0 and rec.year > 0 and rec.day == 0:
                                    months = rec.month
                                    available_days = (rec.year * 12) + months
                                if available_days > 5:
                                    after_available = available_days - 60
                                    value = (rec.eos_total_amount / 12) * after_available
                                    value2 = (rec.eos_total_amount / 24) * 60
                                    rec.value = value + value2
                        else:
                            if rec.end_of_service:
                                end_of_service = datetime(rec.end_of_service.year, rec.end_of_service.month,
                                                          calendar.mdays[rec.end_of_service.month])
                                days_end_date = end_of_service.day
                                available_days = 0
                                day_in_months = 0
                                if rec.month > 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = rec.month + day_in_months

                                elif rec.month == 0 and rec.year > 0:
                                    if rec.day > 0:
                                        day_in_months = rec.day / days_end_date
                                    available_days = (rec.year * 12) + day_in_months

                                elif rec.month == 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = round(day_in_months)

                                elif rec.month > 0 and rec.year > 0 and rec.day > 0:
                                    day = rec.day / days_end_date
                                    months = rec.month + day
                                    available_days = (rec.year * 12) + months

                                elif rec.month > 0 and rec.year > 0 and rec.day == 0:
                                    months = rec.month
                                    available_days = (rec.year * 12) + months

                                rec.value = (rec.eos_total_amount / 24) * available_days

                    else:
                        if rec.end_of_service:
                            end_of_service = datetime(rec.end_of_service.year, rec.end_of_service.month,
                                                      calendar.mdays[rec.end_of_service.month])
                            days_end_date = end_of_service.day
                            available_days = 0
                            day_in_months = 0
                            if rec.month > 0 and rec.year == 0:
                                day_in_months = rec.day / days_end_date
                                available_days = rec.month + day_in_months

                            elif rec.month == 0 and rec.year > 0:
                                if rec.day > 0:
                                    day_in_months = rec.day / days_end_date
                                available_days = (rec.year * 12) + day_in_months

                            elif rec.month == 0 and rec.year == 0:
                                day_in_months = rec.day / days_end_date
                                available_days = round(day_in_months)

                            elif rec.month > 0 and rec.year > 0 and rec.day > 0:
                                day = rec.day / days_end_date
                                months = rec.month + day
                                available_days = (rec.year * 12) + months

                            elif rec.month > 0 and rec.year > 0 and rec.day == 0:
                                months = rec.month
                                available_days = (rec.year * 12) + months
                            if available_days > 5:
                                after_available = available_days - 60
                                value = (rec.eos_total_amount / 12) * after_available
                                value2 = (rec.eos_total_amount / 24) * 60
                                rec.value = value + value2
            elif rec.contract_type == 'unlimited_period':
                if rec.reason_id.id == self.env.ref('gs_hr_eos.gs_end_reason14').id \
                        and rec.reason_id.id == self.env.ref('gs_hr_eos.gs_end_reason10').id:
                    rec.value = 0
                elif rec.reason_id.id == self.env.ref('gs_hr_eos.gs_end_reason11').id:
                    if rec.year < 2:
                        rec.value = 0
                    elif 2 <= rec.year <= 5:
                        if rec.year == 5 and rec.month == 0 and rec.day == 0:
                            if rec.end_of_service:
                                end_of_service = datetime(rec.end_of_service.year, rec.end_of_service.month,
                                                          calendar.mdays[rec.end_of_service.month])
                                days_end_date = end_of_service.day
                                available_days = 0
                                day_in_months = 0
                                day2 = 0
                                if rec.month > 0 and rec.year == 2:
                                    day_in_months = rec.day / days_end_date
                                    month = (rec.month + day_in_months) / 12
                                    available_days = rec.year + month

                                elif rec.month == 0 and rec.year == 2 and rec.day == 0:
                                    available_days = rec.year

                                elif rec.month == 0 and rec.year > 2:
                                    if rec.day > 0:
                                        day_in_months = rec.day / days_end_date
                                        day2 = day_in_months / 12
                                    available_days = rec.year + day2

                                elif rec.month > 0 and rec.year > 0 and rec.day > 0:
                                    day = rec.day / days_end_date
                                    months = rec.month + day
                                    months2 = months / 12
                                    available_days = rec.year + months2

                                elif rec.month > 0 and rec.year > 0 and rec.day == 0:
                                    months = rec.month / 12
                                    available_days = rec.year + months

                                rec.value = (rec.eos_total_amount / 6) * available_days
                        elif rec.year < 5:
                            if rec.end_of_service:
                                end_of_service = datetime(rec.end_of_service.year, rec.end_of_service.month,
                                                          calendar.mdays[rec.end_of_service.month])
                                days_end_date = end_of_service.day
                                available_days = 0
                                day_in_months = 0
                                day2 = 0
                                if rec.month > 0 and rec.year == 2:
                                    day_in_months = rec.day / days_end_date
                                    month = (rec.month + day_in_months) / 12
                                    available_days = rec.year + month

                                elif rec.month == 0 and rec.year == 2 and rec.day == 0:
                                    available_days = rec.year

                                elif rec.month == 0 and rec.year == 2 and rec.day > 0:
                                    day_in_months = rec.day / days_end_date
                                    month = (rec.month + day_in_months) / 12
                                    available_days = rec.year + month

                                elif rec.month == 0 and rec.year > 2:
                                    if rec.day > 0:
                                        day_in_months = rec.day / days_end_date
                                        day2 = day_in_months / 12
                                    available_days = rec.year + day2

                                elif rec.month > 0 and rec.year > 0 and rec.day > 0:
                                    day = rec.day / days_end_date
                                    months = rec.month + day
                                    months2 = months / 12
                                    available_days = rec.year + months2

                                elif rec.month > 0 and rec.year > 0 and rec.day == 0:
                                    months = rec.month / 12
                                    available_days = rec.year + months

                                rec.value = (rec.eos_total_amount / 6) * available_days
                        else:
                            if rec.end_of_service:
                                end_of_service = datetime(rec.end_of_service.year, rec.end_of_service.month,
                                                          calendar.mdays[rec.end_of_service.month])
                                days_end_date = end_of_service.day
                                available_days = 0
                                day_in_months = 0
                                if rec.month > 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = rec.month + day_in_months

                                elif rec.month == 0 and rec.year > 0:
                                    if rec.day > 0:
                                        day_in_months = rec.day / days_end_date
                                    available_days = (rec.year * 12) + day_in_months

                                elif rec.month == 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = round(day_in_months)

                                elif rec.month > 0 and rec.year > 0 and rec.day > 0:
                                    day = rec.day / days_end_date
                                    months = rec.month + day
                                    available_days = (rec.year * 12) + months

                                elif rec.month > 0 and rec.year > 0 and rec.day == 0:
                                    months = rec.month
                                    available_days = (rec.year * 12) + months
                                if available_days > 5:
                                    after_available = available_days - 60
                                    value = (rec.eos_total_amount / 12) * after_available
                                    value2 = (rec.eos_total_amount / 24) * 60
                                    rec.value = (value + value2) * 0.666666667

                    elif 5 <= rec.year < 10:
                        if rec.end_of_service:
                            end_of_service = datetime(rec.end_of_service.year, rec.end_of_service.month,
                                                      calendar.mdays[rec.end_of_service.month])
                            days_end_date = end_of_service.day
                            available_days = 0
                            day_in_months = 0
                            if rec.month > 0 and rec.year == 0:
                                day_in_months = rec.day / days_end_date
                                available_days = rec.month + day_in_months

                            elif rec.month == 0 and rec.year > 0:
                                if rec.day > 0:
                                    day_in_months = rec.day / days_end_date
                                available_days = (rec.year * 12) + day_in_months

                            elif rec.month == 0 and rec.year == 0:
                                day_in_months = rec.day / days_end_date
                                available_days = round(day_in_months)

                            elif rec.month > 0 and rec.year > 0 and rec.day > 0:
                                day = rec.day / days_end_date
                                months = rec.month + day
                                available_days = (rec.year * 12) + months

                            elif rec.month > 0 and rec.year > 0 and rec.day == 0:
                                months = rec.month
                                available_days = (rec.year * 12) + months
                            if available_days > 5:
                                after_available = available_days - 60
                                value = (rec.eos_total_amount / 12) * after_available
                                value2 = (rec.eos_total_amount / 24) * 60
                                rec.value = (value + value2) * 0.666666667
                    elif rec.year >= 10:
                        if rec.end_of_service:
                            end_of_service = datetime(rec.end_of_service.year, rec.end_of_service.month,
                                                      calendar.mdays[rec.end_of_service.month])
                            days_end_date = end_of_service.day
                            available_days = 0
                            day_in_months = 0
                            if rec.month > 0 and rec.year == 0:
                                day_in_months = rec.day / days_end_date
                                available_days = rec.month + day_in_months

                            elif rec.month == 0 and rec.year > 0:
                                if rec.day > 0:
                                    day_in_months = rec.day / days_end_date
                                available_days = (rec.year * 12) + day_in_months

                            elif rec.month == 0 and rec.year == 0:
                                day_in_months = rec.day / days_end_date
                                available_days = round(day_in_months)

                            elif rec.month > 0 and rec.year > 0 and rec.day > 0:
                                day = rec.day / days_end_date
                                months = rec.month + day
                                available_days = (rec.year * 12) + months

                            elif rec.month > 0 and rec.year > 0 and rec.day == 0:
                                months = rec.month
                                available_days = (rec.year * 12) + months
                            if available_days > 5:
                                after_available = available_days - 60
                                value = (rec.eos_total_amount / 12) * after_available
                                value2 = (rec.eos_total_amount / 24) * 60
                                rec.value = value + value2
                else:
                    if rec.year <= 5:
                        if rec.year == 5 and rec.month > 0 and rec.day > 0:
                            if rec.end_of_service:
                                end_of_service = datetime(rec.end_of_service.year, rec.end_of_service.month,
                                                          calendar.mdays[rec.end_of_service.month])
                                days_end_date = end_of_service.day
                                available_days = 0
                                day_in_months = 0
                                if rec.month > 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = rec.month + day_in_months

                                elif rec.month == 0 and rec.year > 0:
                                    if rec.day > 0:
                                        day_in_months = rec.day / days_end_date
                                    available_days = (rec.year * 12) + day_in_months

                                elif rec.month == 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = round(day_in_months)

                                elif rec.month > 0 and rec.year > 0 and rec.day > 0:
                                    day = rec.day / days_end_date
                                    months = rec.month + day
                                    available_days = (rec.year * 12) + months

                                elif rec.month > 0 and rec.year > 0 and rec.day == 0:
                                    months = rec.month
                                    available_days = (rec.year * 12) + months
                                if available_days > 5:
                                    after_available = available_days - 60
                                    value = (rec.eos_total_amount / 12) * after_available
                                    value2 = (rec.eos_total_amount / 24) * 60
                                    rec.value = value + value2
                        elif rec.year == 5 and rec.month > 0 and rec.day == 0:
                            if rec.end_of_service:
                                end_of_service = datetime(rec.end_of_service.year, rec.end_of_service.month,
                                                          calendar.mdays[rec.end_of_service.month])
                                days_end_date = end_of_service.day
                                available_days = 0
                                day_in_months = 0
                                if rec.month > 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = rec.month + day_in_months

                                elif rec.month == 0 and rec.year > 0:
                                    if rec.day > 0:
                                        day_in_months = rec.day / days_end_date
                                    available_days = (rec.year * 12) + day_in_months

                                elif rec.month == 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = round(day_in_months)

                                elif rec.month > 0 and rec.year > 0 and rec.day > 0:
                                    day = rec.day / days_end_date
                                    months = rec.month + day
                                    available_days = (rec.year * 12) + months

                                elif rec.month > 0 and rec.year > 0 and rec.day == 0:
                                    months = rec.month
                                    available_days = (rec.year * 12) + months
                                if available_days > 5:
                                    after_available = available_days - 60
                                    value = (rec.eos_total_amount / 12) * after_available
                                    value2 = (rec.eos_total_amount / 24) * 60
                                    rec.value = value + value2
                        elif rec.year == 5 and rec.month == 0 and rec.day > 0:
                            if rec.end_of_service:
                                end_of_service = datetime(rec.end_of_service.year, rec.end_of_service.month,
                                                          calendar.mdays[rec.end_of_service.month])
                                days_end_date = end_of_service.day
                                available_days = 0
                                day_in_months = 0
                                if rec.month > 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = rec.month + day_in_months

                                elif rec.month == 0 and rec.year > 0:
                                    if rec.day > 0:
                                        day_in_months = rec.day / days_end_date
                                    available_days = (rec.year * 12) + day_in_months

                                elif rec.month == 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = round(day_in_months)

                                elif rec.month > 0 and rec.year > 0 and rec.day > 0:
                                    day = rec.day / days_end_date
                                    months = rec.month + day
                                    available_days = (rec.year * 12) + months

                                elif rec.month > 0 and rec.year > 0 and rec.day == 0:
                                    months = rec.month
                                    available_days = (rec.year * 12) + months
                                if available_days > 5:
                                    after_available = available_days - 60
                                    value = (rec.eos_total_amount / 12) * after_available
                                    value2 = (rec.eos_total_amount / 24) * 60
                                    rec.value = value + value2
                        else:
                            if rec.end_of_service:
                                end_of_service = datetime(rec.end_of_service.year, rec.end_of_service.month,
                                                          calendar.mdays[rec.end_of_service.month])
                                days_end_date = end_of_service.day
                                available_days = 0
                                day_in_months = 0
                                if rec.month > 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = rec.month + day_in_months

                                elif rec.month == 0 and rec.year > 0:
                                    if rec.day > 0:
                                        day_in_months = rec.day / days_end_date
                                    available_days = (rec.year * 12) + day_in_months

                                elif rec.month == 0 and rec.year == 0:
                                    day_in_months = rec.day / days_end_date
                                    available_days = round(day_in_months)

                                elif rec.month > 0 and rec.year > 0 and rec.day > 0:
                                    day = rec.day / days_end_date
                                    months = rec.month + day
                                    available_days = (rec.year * 12) + months

                                elif rec.month > 0 and rec.year > 0 and rec.day == 0:
                                    months = rec.month
                                    available_days = (rec.year * 12) + months

                                rec.value = (rec.eos_total_amount / 24) * available_days

                    else:
                        if rec.end_of_service:
                            end_of_service = datetime(rec.end_of_service.year, rec.end_of_service.month,
                                                      calendar.mdays[rec.end_of_service.month])
                            days_end_date = end_of_service.day
                            available_days = 0
                            day_in_months = 0
                            if rec.month > 0 and rec.year == 0:
                                day_in_months = rec.day / days_end_date
                                available_days = rec.month + day_in_months

                            elif rec.month == 0 and rec.year > 0:
                                if rec.day > 0:
                                    day_in_months = rec.day / days_end_date
                                available_days = (rec.year * 12) + day_in_months

                            elif rec.month == 0 and rec.year == 0:
                                day_in_months = rec.day / days_end_date
                                available_days = round(day_in_months)

                            elif rec.month > 0 and rec.year > 0 and rec.day > 0:
                                day = rec.day / days_end_date
                                months = rec.month + day
                                available_days = (rec.year * 12) + months

                            elif rec.month > 0 and rec.year > 0 and rec.day == 0:
                                months = rec.month
                                available_days = (rec.year * 12) + months
                            if available_days > 5:
                                after_available = available_days - 60
                                value = (rec.eos_total_amount / 12) * after_available
                                value2 = (rec.eos_total_amount / 24) * 60
                                rec.value = value + value2

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            contract = self.env['hr.contract'].search(
                [('state', '=', 'open'), ('employee_id', '=', rec.employee_id.id)], limit=1)
            rec.eos_total_amount = contract.eos_total_amount

    @api.onchange('end_of_service')
    def _onchange_end_of_service(self):
        if self.end_of_service:
            rd = relativedelta(self.end_of_service, self.joining_date)
            self.service_period = str(rd.years) + ' Years & ' + str(rd.months) + ' Months & ' + str(
                rd.days) + ' Days'
            self.year = rd.years
            self.month = rd.months
            self.day = rd.days

    # @api.model
    # def create(self, vals):
    #     res = super(GsEOS, self).create(vals)
    #     res.get_name()
    #     res.set_end_of_service()
    #     return res

    def set_end_of_service(self):
        for rec in self:
            contract = self.env['hr.contract'].search(
                [('state', '=', 'open'), ('employee_id', '=', rec.employee_id.id)], limit=1)
            if rec.end_of_service:
                contract.eos_date = rec.end_of_service

    def get_name(self):
        for rec in self:
            rec.name = "End of service for " + str(rec.employee_id.name)
