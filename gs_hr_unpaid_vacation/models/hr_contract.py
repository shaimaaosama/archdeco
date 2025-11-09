from dateutil.relativedelta import relativedelta
from datetime import date
from odoo import api, models, _, fields
from odoo.exceptions import ValidationError

class HrContractInherit(models.Model):
    _inherit = 'hr.contract'

    unpaid_vacation_ids = fields.One2many('gs.unpaid.vacation', 'contract_id', string='Unpaid Vacation',)
    vacation_state = fields.Selection(
        selection=[
            ('unpaid_vacation', 'Unpaid Vacation'),
        ],
        required=False, )

    def _cron_check_vacation(self):
        today = fields.Date.today()
        unpaid_vacation = self.env['gs.unpaid.vacation'].search([('start_date', '<=', today),('end_date', '>=', today)])
        if unpaid_vacation:
            for vac in unpaid_vacation:
                vac.contract_id.vacation_state = 'unpaid_vacation'

    def _cron_check_vacation_end(self):
        today = fields.Date.today()
        contracts_on_vacation = self.env['hr.contract'].search([('vacation_state', '=', 'unpaid_vacation'), ('date_end', '>=', today)])
        for contract in contracts_on_vacation:
            unpaid_vacation = self.env['gs.unpaid.vacation'].search([
                ('contract_id', '=', contract.id),
                ('start_date', '<=', today),
                ('end_date', '>=', today)
            ])
            if not unpaid_vacation:
                contract.vacation_state = False


    gosi_wage = fields.Float(string='Gosi Wage')
    gosi_housing = fields.Float(string='Gosi Housing')
    gosi_allowance = fields.Float(string='GOSI other allowances')





class UnpaidVacation(models.Model):
    _name = 'gs.unpaid.vacation'
    
    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for rec in self:
            if rec.end_date:
                period_days = relativedelta(rec.end_date, rec.start_date)
                rec.years = period_days.years
                rec.months = period_days.months
                rec.days = period_days.days
                period = period_days.years + (period_days.months / 12.0) + (period_days.days / 365.0)
                rec.duration = period
                
    contract_id = fields.Many2one('hr.contract')
    employee_id = fields.Many2one('hr.employee', related='contract_id.employee_id')
    start_date = fields.Date(string="Start Date",)
    end_date = fields.Date(string="End Date",)
    duration = fields.Float(string='Duration', compute=_compute_duration, store=True)
    years = fields.Integer(string="Years", compute=_compute_duration, store=True)
    months = fields.Integer(string="Months", compute=_compute_duration, store=True)
    days = fields.Integer(string="Days", compute=_compute_duration, store=True)


class HREndServiceBenInherit(models.Model):
    _inherit = 'hr.end.service.benefit'

    @api.depends('hiring_date', 'date', 'employee_id')
    def _compute_period(self):
        for record in self:
            duration = 0
            if record.hiring_date:
                unpaid_vacation = self.env['gs.unpaid.vacation'].search([('employee_id', '=', record.employee_id.id)])
                if unpaid_vacation:
                    for vac in unpaid_vacation:
                        duration += vac.years * 365
                        duration += vac.months * 12
                        duration += vac.days

                    hiring_date = record.hiring_date
                    period_days = relativedelta(record.date + relativedelta(days=1), hiring_date)
                    adjusted_date = record.date - relativedelta(days=duration)
                    adjusted_period_days = relativedelta(adjusted_date, hiring_date)

                    record.years = adjusted_period_days.years
                    record.months = adjusted_period_days.months
                    record.days = adjusted_period_days.days

                    period = period_days.years + (period_days.months / 12.0) + (period_days.days / 365.0)
                    record.service_period = period
                else:
                    hiring_date = record.hiring_date
                    period_days = relativedelta(record.date + relativedelta(days=1), hiring_date)
                    record.years = period_days.years
                    record.months = period_days.months
                    record.days = period_days.days
                    period = period_days.years + (period_days.months / 12.0) + (period_days.days / 365.0)
                    record.service_period = period


    years = fields.Integer(string="Years", compute=_compute_period, store=True)
    months = fields.Integer(string="Months", compute=_compute_period, store=True)
    days = fields.Integer(string="Days", compute=_compute_period, store=True)
    service_period = fields.Float(string="Service Period In Years", compute=_compute_period, store=True)


class HRPayslipInherit(models.Model):
    _inherit = 'hr.payslip'

    def compute_sheet(self):
        for rec in self:
            if rec.employee_id:
                unpaid_vacation = self.env['gs.unpaid.vacation'].search([('employee_id', '=', rec.employee_id.id),('start_date', '<=', rec.date_from), ('end_date', '>=', rec.date_to)])
                if unpaid_vacation:
                    raise ValidationError("This employee has unpaid vacation")
            return super(HRPayslipInherit,self).compute_sheet()