# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'
    
    building_no = fields.Char(string='Building No',)
    addition_no = fields.Char(string='Addition No',)
    unit_no = fields.Char(string='Unit No',)


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    is_get_data_notification = fields.Boolean()

    @api.onchange('date_end')
    def onchange_method(self):
        allocation_model_available = self.env.registry.get('hr.leave.allocation')
        for rec in self:
            if rec.is_get_data_notification:
                rec.is_get_data_notification = False
                employee = self.env['hr.employee'].search([('id', '=', rec.employee_id.id)])
                employee.is_get_data_notification = False
            if allocation_model_available and rec.employee_id:
                allocation = self.env['hr.leave.allocation'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('allocation_type', '=', 'accrual'),
                ])
                if allocation:
                    for rex in allocation:
                        rex.date_to = rec.date_end
                        rex.nextcall = False
                        rex.lastcall = rex.date_from
                        rex.number_of_days = 0.0
                        rex._process_accrual_plans(rex.date_to)

    def check_contract(self):
        contract = self.search([('date_end', '!=', False)])
        if contract:
            for rec in contract:
                rec.onchange_method()


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    # @api.model
    # def create(self, vals):
    #     res = super(hr_employee, self).create(vals)
    #     self._get_address_id()
    #     return res

    address_home_id = fields.Many2one(
        'res.partner', 'Address', help='Enter here the private address of the employee, not the one linked to your company.',
        groups="hr.group_hr_user", tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    is_readonly = fields.Boolean()

    @api.onchange('job_id')
    def _onchange_job_id(self):
        for rec in self:
            if rec.job_id:
                contract = self.env['hr.contract'].search([('employee_id', '=', rec._origin.id),('state', '=', 'open')], limit=1)
                contract.job_id = rec.job_id.id
                rec.job_title = rec.job_id.name

    def _compute_address_home_id(self):
        for rec in self:
            pass
            # if self.env.user.has_group('base.group_system'):
            #     rec.is_readonly = True
            # partner = self.env['res.partner'].search([('name', '=', rec.name)], limit=1)
            # rec.address_home_id = partner.id

    work_ext = fields.Char(string="Work Ext", required=False, )
    emergency_contact_2 = fields.Char(string="Emergency Contact 2", required=False, )
    emergency_phone_2 = fields.Char(string="Emergency Phone 2", required=False, )
    type = fields.Selection(string="Bail type",
                            selection=[('sponsorship_system', 'Sponsorship System'), ('hire_system', 'Hire System'),
                                       ('external_warranty', 'External Warranty'), ('saudi', 'Saudi'),
                                       ('not_saudi', 'Non Saudi')], required=False, )
    old_sponsor_name = fields.Char(string="Old Sponsor Name", required=False, )
    sponsor_name = fields.Char(string="Sponsor Name", required=False, store=True)
    bail_type_id = fields.Many2one('gs.bail.type', string='Bail Type')

    employee_owner_number = fields.Char(string="Owner Sponsor Number", required=False, store=True)
    sponsor_number = fields.Char(string="Sponsor Reference Number", required=False, store=True)
    lease_contract_number = fields.Char(string="Lease Contract Number", required=False, )
    arabic_name = fields.Char(string="Employee Arabic Name", required=False, )
    building_number = fields.Char(string="Building Number", required=False, )
    mail_box = fields.Char(string="Mail Box", required=False, )
    area = fields.Char(string="Area", required=False, )
    city_sr = fields.Char(string="City", required=False, )
    additional_zip_code = fields.Char(string="Additional Zip Code", required=False, )
    pants_Length = fields.Char(string="Pants Length", required=False, )
    pants_width = fields.Char(string="Pants Width", required=False, )
    shoes_size = fields.Char(string="Shoes Size", required=False, )
    coat_chest = fields.Char(string="Coat Chest", required=False, )
    coat_length = fields.Char(string="Coat Length", required=False, )
    coat_shoulders = fields.Char(string="Coat Shoulders", required=False, )
    coat_sleeves = fields.Char(string="Coat Sleeves", required=False, )
    t_shirt_chest = fields.Char(string="T-Shirt Chest", required=False, )
    t_shirt_length = fields.Char(string="T-Shirt Length", required=False, )
    t_shirt_shoulders = fields.Char(string="T-Shirt Shoulders", required=False, )
    t_shirt_sleeves = fields.Char(string="T-Shirt Sleeves", required=False, )
    is_sizes = fields.Boolean(string='Uniform?',)
    is_driving_license = fields.Boolean(string='Driving License?',)
    issuer_driving_license = fields.Char(string="Driving License Issuer", )
    d_l_attachment_id = fields.Many2many('ir.attachment', 'd_l_attachment_id03', 'd_l_attachment_id003', 'd_l_attachment_id0003',
                                        string="Driving License Attachment", help='Attachment of Driving License')
    expiry_driving_license_date = fields.Date(string='Driving License Expiry Date', help='Expiry date of Driving License')
    expiry_driving_license_date_new = fields.Date(string='Expiry Date Driving License', help='Expiry date of Driving License')
    type_of_license_id= fields.Many2one('gs.type.of.license', string='Type of license')

    driving_license_restriction_id = fields.Many2one('gs.driving.license.restriction', string='Restriction',)
    is_authority_membership = fields.Boolean(string='Authority membership?', )
    authority_membership_no = fields.Char(string='Membership Number')
    a_m_attachment_id = fields.Many2many('ir.attachment', 'a_m_attachment_id03', 'a_m_attachment_id003',
                                         'a_m_attachment_id0003',
                                         string="Authority Membership Attachment", help='Attachment of Authority Membership')
    expiry_date = fields.Date(string='Authority Membership Expiry Date', help='Expiry date of Authority Membership')
    expiry_date_authority_membership = fields.Date(string='Expiry Date Authority Membership', help='Expiry date of Authority Membership')

    type_of_authority = fields.Many2one('gs.type.of.membership', string='Type of Authority')
    residence_profession = fields.Many2one('gs.residence.profession', string='IQAMA Profession',)
    issuer_identification = fields.Char(string="Issuer Place", )
    expiry_date_identification = fields.Date(string='Identification Expiry Date',)
    expiry_date_identification_new = fields.Date(string='Expiry Date Identification',)
    balady_date = fields.Date(string='Balady Training Date (Gregorian)')


    is_medical_card = fields.Boolean(string='Balady Card?',)
    balady_card_num = fields.Char(string="Balady Card Reference No.", )
    training_end_date = fields.Date(string='Balady Training End Date')
    baladyl_card_end_date = fields.Date(string='Balady Card End Date')

    training_end_date_hijri = fields.Char(string='Balady Training End Date (Hijri)')
    baladyl_card_end_date_hijri = fields.Char(string='Balady Card End Date (Hijri)')

    # @api.onchange('training_end_date','baladyl_card_end_date')
    # def date_in_arabic(self):
    #     if self.training_end_date:
    #         self.training_end_date_hijri = 'هـ'+ HijriDate.get_hijri_date(self.training_end_date)
    #     if self.baladyl_card_end_date:
    #         self.baladyl_card_end_date_hijri = 'هـ' + HijriDate.get_hijri_date(self.baladyl_card_end_date)

    issuer_medical_card = fields.Char(string="Balady Card Issuer", )
    m_c_attachment_id = fields.Many2many('ir.attachment', 'm_c_attachment_id03', 'm_c_attachment_id003', 'm_c_attachment_id0003',
                                        string="Medical Card Attachment", help='Attachment of Balady Card')
    expiry_medical_card_date = fields.Date(string='Balady Card Expiry Date', help='Expiry date of Balady Card')
    expiry_date_medical_card_new = fields.Date(string='Expiry Date Medical Card', help='Expiry date of Medical Card')

    is_get_data_notification = fields.Boolean()

    is_get_id_expiry_date = fields.Boolean()
    is_get_expiry_driving_license = fields.Boolean()
    is_get_passport_expiry = fields.Boolean()
    is_get_expiry_medical_card = fields.Boolean()
    graduation_year = fields.Selection([(str(x), str(x)) for x in range(1800, 2050)], string='Graduation Year', required=False)

    @api.onchange('id_expiry_date_new', 'expiry_driving_license_date_new', 'passport_expiry_date', 'expiry_date_medical_card_new')
    def onchange_method(self):
        if self.is_get_data_notification:
            self.is_get_data_notification = False

    @api.onchange('id_expiry_date_new')
    def onchange_id_expiry_date(self):
        if self.is_get_id_expiry_date:
            self.is_get_id_expiry_date = False

    @api.onchange('is_get_expiry_driving_license')
    def onchange_is_get_expiry_driving_license(self):
        if self.is_get_expiry_driving_license:
            self.is_get_expiry_driving_license = False

    @api.onchange('is_get_passport_expiry')
    def onchange_is_get_passport_expiry(self):
        if self.is_get_passport_expiry:
            self.is_get_passport_expiry = False

    @api.onchange('is_get_expiry_medical_card')
    def onchange_is_get_expiry_medical_card(self):
        if self.is_get_expiry_medical_card:
            self.is_get_expiry_medical_card = False
