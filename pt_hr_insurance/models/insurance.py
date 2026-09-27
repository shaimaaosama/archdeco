# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime
import calendar


class GsInsurance(models.Model):
    _name = 'gs.insurance'
    _description = 'Employee Insurance'

    _sql_constraints = [
        ('beneficiary_insurance_id_uniq', 'unique (beneficiary_insurance_id)',
         """Beneficiary Insurance ID already exists!"""),
    ]

    name = fields.Char(string='Name', )
    type = fields.Selection(string='Type', selection=[('original', 'Original'), ('follower', 'Follower'), ], default='original')

    employee_id = fields.Many2one('hr.employee', string='Employee')
    country_employee_id = fields.Many2one('res.country', 'Employee Nationality',)
    identity_employee_number = fields.Char(string='Employee Identity Number',)
    id_expiry_employee_date = fields.Date(string='Employee ID Expiry Date', help='Expiry date of Identification ID')
    id_attachment_employee_id = fields.Many2many('ir.attachment', 'id_attachment_employee_id01', 'id_attachment_employee_id001', 'id_attachment_employee_id0001',
                                        string="Employee ID Attachment", help='Expiry date of Identification ID')
    marital_employee = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Employee Marital Status', default='single')

    birth_date_employee = fields.Date(string="Employee Date of Birth",)
    member_age_employee = fields.Char(string='Employee Age', required=False)
    gender_employee = fields.Selection(string='Employee Gender', selection=[('male', 'Male'), ('female', 'Female'), ])
    relation_employee_id = fields.Many2one('hr.employee.relation', string="Employee Relation", help="Relationship with the employee")

    follower_id = fields.Many2one('gs.follower', string='Follower')
    birth_date = fields.Date(string="Follower Date of Birth",)
    identity_number = fields.Char(string='Follower Identity Number',)
    id_expiry_date = fields.Date(string='Follower ID Expiry Date', help='Expiry date of Identity Number')
    id_attachment_id = fields.Many2many('ir.attachment', 'id_attachment_id01', 'id_attachment_id001', 'id_attachment_id0001',
                                        string="Follower ID Attachment", help='Attachment of Identification ID' )
    country_id = fields.Many2one('res.country', 'Follower Nationality',)
    member_age = fields.Char(string='Follower Age', required=False)
    gender = fields.Selection(string='Follower Gender', selection=[('male', 'Male'), ('female', 'Female'), ])
    main_membership = fields.Char(string='Main Membership No.',)
    relation_id = fields.Many2one('hr.employee.relation', string="Follower Relation", help="Relationship with the employee")
    marital_follower = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Follower Marital Status', default='single')

    insurance_network_id = fields.Many2one('gs.insurance.network', string="Insurance Network")
    policy_number_id = fields.Many2one('gs.insurance.contract', string='Policy Number', help="Insurance Contract No.")
    sponsor = fields.Char(string='Sponsor ID', )

    insurance_class_id = fields.Many2one('gs.insurance.class', 'Insurance Class',)
    annual_amount = fields.Integer(string='Annual Amount',)
    start_date = fields.Date(string="Start Date",)
    end_date = fields.Date(string="End Date",)
    actual_amount = fields.Integer(string='Actual Amount',)
    policy_amount = fields.Integer(string='Policy Amount',)
    vat = fields.Char(string='VAT', )
    bill_id = fields.Many2one('account.move', string='Bill No',)
    claim_ref = fields.Char(string='Claim Ref', )
    claim_date = fields.Date(string='Claim Date', )
    invoice_number_id = fields.Many2one('account.move', string='Invoice Number',)
    active_member = fields.Boolean(string='Active Member')
    clearance = fields.Boolean(string='Clearance')
    cl_attachment_id = fields.Many2many('ir.attachment', 'cl_attachment_id01', 'cl_attachment_id001', 'cl_attachment_id0001',
                                        string="Clearance Attachment",)
    duration = fields.Char(string='Duration',)
    beneficiary_insurance_id = fields.Char(string='Beneficiary Insurance ID',)

    addition_date = fields.Date(string='Addition Date', )
    po_number = fields.Char(string='PO Number',)
    po_date = fields.Date(string='PO Date', )
    declining_date = fields.Date(string='Declining Date', )
    decline_period = fields.Char(string='Decline Period',)
    refund_amount = fields.Integer(string='Refund Amount')
    sub_date = fields.Float(string='Sub Date')

    @api.onchange('start_date')
    def _onchange_start_date(self):
        for rec in self:
            if not rec.addition_date:
                rec.addition_date = rec.start_date

    @api.onchange('declining_date', 'end_date')
    def _onchange_declining_date2(self):
        if self.declining_date and self.end_date:
            rd = relativedelta(self.end_date, self.declining_date)
            self.decline_period = str(rd.years) + ' Years & ' + str(rd.months) + ' Months & ' + str(
                rd.days) + ' Days'

    @api.onchange('declining_date', 'end_date')
    def _onchange_declining_date(self):
        for rec in self:
            if rec.end_date:
                end_date = datetime(rec.end_date.year, rec.end_date.month, calendar.mdays[rec.end_date.month])
                days_end_date = end_date.day
                available_days = 0
                day_in_months = 0
                rd = relativedelta(rec.end_date, rec.declining_date)
                if rd.months > 0 and rd.years == 0:
                    day_in_months = rd.days / days_end_date
                    available_days = rd.months + day_in_months

                elif rd.months == 0 and rd.years > 0:
                    if rd.days > 0:
                        day_in_months = rd.days / days_end_date
                    available_days = (rd.years * 12) + day_in_months

                elif rd.months == 0 and rd.years == 0:
                    day_in_months = rd.days / days_end_date
                    available_days = round(day_in_months)

                elif rd.months > 0 and rd.years > 0 and rd.days > 0:
                    day = rd.days / days_end_date
                    months = rd.months + day

                    available_days = (rd.years * 12) + months

                ##### New
                wy = relativedelta(rec.end_date, rec.addition_date)
                available_days2 = 0
                day_in_months2 = 0
                if wy.months > 0 and wy.years == 0:
                    day_in_months2 = wy.days / days_end_date
                    available_days2 = wy.months + day_in_months2

                elif wy.months == 0 and wy.years > 0:
                    if wy.days > 0:
                        day_in_months2 = wy.days / days_end_date
                    available_days2 = (wy.years * 12) + day_in_months2

                elif wy.months == 0 and wy.years == 0:
                    day_in_months2 = wy.days / days_end_date
                    available_days2 = round(day_in_months2)

                elif wy.months > 0 and wy.years > 0 and wy.days > 0:
                    day = wy.days / days_end_date
                    months = wy.months + day

                    available_days2 = (wy.years * 12) + months
                if rec.sub_date:
                    x = available_days
                    y = rec.actual_amount / available_days2

                    # amount = rec.annual_amount / rec.sub_date
                    # rec.refund_amount = available_days * amount
                    rec.refund_amount = x * y

    @api.onchange('policy_number_id', 'employee_id')
    def _onchange_policy_number_id(self):
        if self.policy_number_id and self.employee_id:
            self.sponsor = self.policy_number_id.company_unique_id
            self.start_date = self.policy_number_id.start_date
            self.end_date = self.policy_number_id.end_date
        elif self.policy_number_id:
            self.start_date = self.policy_number_id.start_date
            self.end_date = self.policy_number_id.end_date

    @api.onchange('employee_id')
    def _onchange_employee_follower_id(self):
        for rec in self:
            if rec.employee_id and rec.type == 'follower':
                insurances = self.env['gs.insurance'].search([('type', '=', 'original'), ('employee_id', '=', rec.employee_id.id)], limit=1)
                rec.main_membership = insurances.beneficiary_insurance_id

    @api.onchange('addition_date', 'end_date')
    def _onchange_birth_date(self):
        if self.addition_date and self.end_date:
            rd = relativedelta(self.end_date, self.addition_date)
            self.duration = str(rd.years) + ' Years & ' + str(rd.months) + ' Months & ' + str(
                rd.days) + ' Days'

    @api.onchange('annual_amount', 'addition_date', 'end_date')
    def _get_actual_amount2(self):
        if self.addition_date and self.end_date:
            end_date = datetime(self.end_date.year, self.end_date.month, calendar.mdays[self.end_date.month])
            days_end_date = end_date.day
            available_days = 0
            day_in_months = 0
            rd = relativedelta(self.end_date, self.addition_date)
            if rd.months > 0 and rd.years == 0:
                day_in_months = rd.days / days_end_date
                available_days = rd.months + day_in_months

            elif rd.months == 0 and rd.years > 0:
                if rd.days > 0:
                    day_in_months = rd.days / days_end_date
                available_days = (rd.years * 12) + day_in_months

            elif rd.months == 0 and rd.years == 0:
                day_in_months = rd.days / days_end_date
                available_days = round(day_in_months)

            elif rd.months > 0 and rd.years > 0 and rd.days > 0:
                day = rd.days / days_end_date
                months = rd.months + day

                available_days = (rd.years * 12) + months
            if self.annual_amount:
                # self.actual_amount = self.annual_amount / available_days
                self.actual_amount = (available_days / 12) * self.annual_amount

    @api.onchange('annual_amount', 'addition_date', 'end_date')
    def _get_actual_amount(self):
        if self.addition_date and self.end_date:
            end_date = datetime(self.end_date.year, self.end_date.month, calendar.mdays[self.end_date.month])
            days_end_date = end_date.day
            available_days = 0
            day_in_months = 0
            rd = relativedelta(self.end_date, self.addition_date)
            if rd.months > 0 and rd.years == 0:
                day_in_months = rd.days / days_end_date
                available_days = rd.months + day_in_months

            elif rd.months == 0 and rd.years > 0:
                if rd.days > 0:
                    day_in_months = rd.days / days_end_date
                available_days = (rd.years * 12) + day_in_months

            elif rd.months == 0 and rd.years == 0:
                day_in_months = rd.days / days_end_date
                available_days = round(day_in_months)

            elif rd.months > 0 and rd.years > 0 and rd.days > 0:
                day = rd.days / days_end_date
                months = rd.months + day

                available_days = (rd.years * 12) + months

            self.sub_date = available_days

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and self.type == 'original':
            self.name = self.employee_id.name
            self.country_employee_id = self.employee_id.country_id.id
            self.identity_employee_number = self.employee_id.identification_id
            self.birth_date_employee = self.employee_id.birthday
            self.member_age_employee = self.employee_id.age
            self.gender_employee = self.employee_id.gender
            self.id_expiry_employee_date = self.employee_id.id_expiry_date_new
            self.id_attachment_employee_id = self.employee_id.id_attachment_id.ids
            self.marital_employee = self.employee_id.marital
        else:
            self.country_employee_id = False
            self.identity_employee_number = False
            self.birth_date_employee = False
            self.member_age_employee = False
            self.gender_employee = False
            self.id_expiry_employee_date = False
            self.id_attachment_employee_id = False
            self.marital_employee = False

    @api.onchange('follower_id')
    def _onchange_follower_id(self):
        if self.follower_id and self.type == 'follower':
            self.name = self.follower_id.name
            self.employee_id = self.follower_id.employee_id.id
            self.country_id = self.follower_id.country_id.id
            self.identity_number = self.follower_id.identity_number
            self.birth_date = self.follower_id.date_of_birth
            self.member_age = self.follower_id.member_age
            self.gender = self.follower_id.gender
            self.id_expiry_date = self.follower_id.id_expiry_date
            self.relation_id = self.follower_id.relation_id.id
            self.id_attachment_id = self.follower_id.id_attachment_id.ids
            self.marital_follower = self.follower_id.marital
        else:
            self.country_id = False
            self.identity_number = False
            self.birth_date = False
            self.member_age = False
            self.gender = False
            self.id_expiry_date = False
            self.relation_id = False
            self.id_attachment_id = False
            self.marital_follower = False
