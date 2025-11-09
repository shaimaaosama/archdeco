# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time


class GsFollower(models.Model):
    _name = 'gs.follower'

    name = fields.Char(string='Name', )
    identity_number = fields.Char(string='Identity Number', )
    id_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Identification ID')
    id_attachment_id = fields.Many2many('ir.attachment', 'id_attachment_id02', 'id_attachment_id002', 'id_attachment_id0002',
                                        string="Identity Attachment", help='Attachment of Identification ID' )

    country_id = fields.Many2one('res.country', 'Nationality')
    date_of_birth = fields.Date(string='Date Of Birth',)
    employee_id = fields.Many2one('hr.employee', string="Employee",)
    insurance = fields.Selection(string='Insurance', selection=[('yas', 'Yas'),('no', 'No'), ], )
    ticket = fields.Selection(string='Ticket', selection=[('yas', 'Yas'),('no', 'No'), ], )
    insurance1 = fields.Boolean(string='Insurance')
    
    ticket1 = fields.Boolean(string='Ticket')
    ticket_type = fields.Selection(string='Ticket', selection=[('economy', 'Economy'), ('business', 'Business'), ], )
    ticket_value = fields.Integer(string='Ticket Value',)
    paid_by_company = fields.Boolean(string='Paid By Company')

    @api.onchange('ticket_type', 'country_id')
    def _onchange_ticket_type(self):
        for rec in self:
            if rec.country_id:
                tickets = self.env['gs.tickets'].search([('country_id', '=', rec.country_id.id)], limit=1)
                if rec.ticket_type == 'economy':
                    self.ticket_value = tickets.economy_fare
                if rec.ticket_type == 'business':
                    self.ticket_value = tickets.business_class_fare

    insurance_class = fields.Char(string='Insurance Class', )
    insurance_class_id = fields.Many2one('gs.insurance.class', string="Insurance Class",)
    border_number = fields.Char(string='Border Number', )

    passport_name_ar = fields.Char(string='Arabic name')
    passport_name_en = fields.Char(string='English name')
    passport_Type = fields.Char(string='Passport Type')
    enlistment_status = fields.Char(string='Enlistment Status')
    job_position = fields.Many2one('hr.job', string="Job in Passport",)
    passport_address = fields.Char(string='Passport Address')
    passport_national_no = fields.Char(string='National No.')

    passport_number = fields.Char(string='Passport Number', )
    passport_country_id = fields.Many2one('res.country', 'Country')
    passport_issue_date = fields.Date(string='Issue date',)
    passport_expiry_date = fields.Date(string='Expiry date',)
    passport_attachment_id = fields.Many2many('ir.attachment', 'passport_attachment_id01', 'passport_attachment_id001', 'passport_attachment_id0001',
                                        string="Passport Attachment", help='Attachment of Passport' )
    type = fields.Char(string='Gender', )
    gender = fields.Selection(string='Gender', selection=[('male', 'Male'), ('female', 'Female'), ])
    relation = fields.Char(string='Relation', )
    relation_id = fields.Many2one('hr.employee.relation', string="Relation", help="Relationship with the employee")
    contact_number = fields.Char(string='Contact Number', )
    street = fields.Char('Street')
    street2 = fields.Char('Street 2')
    city = fields.Char('city')
    zip = fields.Char('zip')
    state_id = fields.Many2one('res.country.state', domain="[('country_id','=?',country_id)]")
    member_age = fields.Char(string='Age', required=False)
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status', default='single')

    @api.onchange('date_of_birth')
    def _onchange_birth_date(self):
        if self.date_of_birth:
            rd = relativedelta(date.today(), self.date_of_birth)
            self.member_age = str(rd.years) + ' Years & ' + str(rd.months) + ' Months & ' + str(
                rd.days) + ' Days'
            # self.member_age_years = str(rd.years) + ' Years'