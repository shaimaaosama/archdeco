# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from datetime import datetime, timedelta
from odoo import models, fields, _, api

GENDER_SELECTION = [('male', 'Male'),
                    ('female', 'Female'),
                    ('other', 'Other')]


class HrEmployeeFamilyInfo(models.Model):
    """Table for keep employee family information"""

    _name = 'hr.employee.family'
    _description = 'HR Employee Family'

    employee_id = fields.Many2one('hr.employee', string="Employee", help='Select corresponding Employee')
    relation_id = fields.Many2one('hr.employee.relation', string="Relation", help="Relationship with the employee")
    member_name = fields.Char(string='Name')
    member_contact = fields.Char(string='Contact No')
    birth_date = fields.Date(string="DOB")

# class HrEmployeePublic(models.Model):
#     _inherit = 'hr.employee.public'
#     personal_mobile = fields.Char(string='Mobile',  help="Personal mobile number of the employee")
#     joining_date = fields.Date(string='Joining Date',
#                                help="Employee joining date computed from the contract start date")
#     id_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Identification ID')
#     id_expiry_date_new = fields.Date(string='Expiry Date Identification ID', help='Expiry date of Identification ID')
#     passport_expiry_date = fields.Date(string='Expiry date', )
#     passport_name_ar = fields.Char(string='Arabic name')
#     passport_name_en = fields.Char(string='English name')
#     issue_date = fields.Date(string='Issued Date', help="Issued Date")
#     passport_issuer = fields.Char(string='Issue Place')
#     passport_Type = fields.Char(string='Passport Type')
#     enlistment_status = fields.Char(string='Enlistment Status')
#     job_position = fields.Many2one('hr.job', string="Job in Passport", )
#     passport_address = fields.Char(string='Passport Address')
#     passport_national_no = fields.Char(string='National No.')
#     is_passport = fields.Boolean(string='Passport?', )
#
#     border_number = fields.Char(string="Border Number", )
#     expiry_border_number_date = fields.Date(string='Entry Date', help='Entry date of Border Number')
#     religion = fields.Selection(
#         [('mus', 'Muslem'), ('non_mus', 'Non Muslem')],
#         string="Religion")
#     follower_id = fields.Many2one('gs.follower', string='Name')
#     follower_count = fields.Integer( string='#follower')
#     work_ext = fields.Char(string="Work Ext ", required=False, )
#     emergency_contact_2 = fields.Char(string="Emergency Contact 2", required=False, )
#     emergency_phone_2 = fields.Char(string="Emergency Phone 2", required=False, )
#     type = fields.Selection(string="Bail type",
#                             selection=[('sponsorship_system', 'Sponsorship System'), ('hire_system', 'Hre System'),
#                                        ('external_warranty', 'External Warranty'), ], required=False, )
#     old_sponsor_name = fields.Char(string="Old Sponsor Name", required=False, )
#     sponsor_name = fields.Char(string="Sponsor Name", required=False, store=True)
#     bail_type_id = fields.Many2one('gs.bail.type', string='Bail Type')
#
#     employee_owner_number = fields.Char(string="Sponsor Number", required=False, store=True)
#     sponsor_number = fields.Char(string="Sponsor Number", required=False, store=True)
#     lease_contract_number = fields.Char(string="Lease Contract Number", required=False, )
#     arabic_name = fields.Char(string="Arabic Name", required=False, )
#     building_number = fields.Char(string="Building Number", required=False, )
#     mail_box = fields.Char(string="mail box", required=False, )
#     area = fields.Char(string="Area", required=False, )
#     city_sr = fields.Char(string="City", required=False, )
#     additional_zip_code = fields.Char(string="Additional Zip Code", required=False, )
#     pants_Length = fields.Char(string=" Pants Length", required=False, )
#     pants_width = fields.Char(string="Pants width", required=False, )
#     shoes_size = fields.Char(string="Shoes Size", required=False, )
#     coat_chest = fields.Char(string="", required=False, )
#     coat_length = fields.Char(string="", required=False, )
#     coat_shoulders = fields.Char(string="", required=False, )
#     coat_sleeves = fields.Char(string="", required=False, )
#     t_shirt_chest = fields.Char(string="", required=False, )
#     t_shirt_length = fields.Char(string="", required=False, )
#     t_shirt_shoulders = fields.Char(string="", required=False, )
#     t_shirt_sleeves = fields.Char(string="", required=False, )
#     is_sizes = fields.Boolean(string='Uniform?', )
#     is_driving_license = fields.Boolean(string='Driving License?', )
#     issuer_driving_license = fields.Char(string="Issuer", )
#
#     expiry_driving_license_date = fields.Date(string='Expiry Date', help='Expiry date of Driving License')
#     expiry_driving_license_date_new = fields.Date(string='Expiry Date Driving License',
#                                                   help='Expiry date of Driving License')
#     type_of_license_id = fields.Many2one('gs.type.of.license', string='Type of license')
#
#     driving_license_restriction_id = fields.Many2one('gs.driving.license.restriction', string='Restriction', )
#     is_authority_membership = fields.Boolean(string='Authority membership?', )
#     authority_membership_no = fields.Char(string='Membership Number')
#
#     expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Authority Membership')
#     expiry_date_authority_membership = fields.Date(string='Expiry Date Authority Membership',
#                                                    help='Expiry date of Authority Membership')
#
#     type_of_authority = fields.Many2one('gs.type.of.membership', string='Type of Authority')
#     residence_profession = fields.Many2one('gs.residence.profession', string='IQAMA Profession', )
#     issuer_identification = fields.Char(string="Issuer Place", )
#     expiry_date_identification = fields.Date(string='Expiry Date ', )
#     expiry_date_identification_new = fields.Date(string='Expiry Date Identification', )
#
#     is_medical_card = fields.Boolean(string='Balady Card?', )
#     issuer_medical_card = fields.Char(string="Issuer", )
#
#     expiry_medical_card_date = fields.Date(string='Expiry Date', help='Expiry date of Driving License')
#     expiry_date_medical_card_new = fields.Date(string='Expiry Date Medical Card', help='Expiry date of Medical Card')
#
#     is_get_data_notification = fields.Boolean()
#
#     is_get_id_expiry_date = fields.Boolean()
#     is_get_expiry_driving_license = fields.Boolean()
#     is_get_passport_expiry = fields.Boolean()
#     is_get_expiry_medical_card = fields.Boolean()
#     education_level_id = fields.Many2one('gs.education.level', string='Education Level', )
#     graduation_year = fields.Selection([(str(x), str(x)) for x in range(1800, 2050)], string='Graduation Year',
#                                        required=False)
#     gosi_number = fields.Char(string='GOSI Number', help="Gosi Number")
#     is_gosi = fields.Boolean(string='Is Gosi?')
#     company_share_per = fields.Float('Company Share %',  store=1)
#     company_share_amount = fields.Float('Company Share Amount',  store=1)
#     employee_share_per = fields.Float('Employee Share %',  store=1)
#     employee_share_amount = fields.Float('Employee Share Amount',  store=1)
#     gosi_salary_amount = fields.Float('Gosi Salary', )
#     maximum_gosi_salary = fields.Float('Maximum Gosi Salary', store=1)
#     gosi_conf = fields.Many2one('gosi.config', readonly=1,)  # default=lambda self: self.env['gosi.config'].search([],limit=1), default=_default_gosi_config,
#     run_com = fields.Boolean()
#     age = fields.Float(string='AGE', digits=(2, 1), store=1)
#     total_package_val = fields.Float(string="Total", )
#     wage = fields.Float('Basic Salary',  tracking=True, help="Employee's monthly gross wage.")
#
# #     ////////////////////////////////////////////
#     house_allowance_val = fields.Float(string="House Amount")
#     trans_allowance_val = fields.Float(string="Transportation Amount")
#     eos_total_amount = fields.Float('EOS Base Amount', )
#     eos_total_amount_month = fields.Float('EOS Monthly')
#     vacation_total_amount = fields.Float('Vacation Base Amount')
#     vacation_total_amount_month = fields.Float('Vacation Monthly')
#     run_compute = fields.Boolean()
#     total_paid = fields.Float(string="Total Paid")
#     other_allowance = fields.Float(string="Other Allowance")
#     ticket_base_amount = fields.Float(string="Ticket Base Amount")
#     ticket_base_amount_month = fields.Float(string="Ticket Monthly")
#     no_of_tickets = fields.Integer(string="No Of Tickets")
#     annual_time_off_accrued = fields.Integer(string="Annual Time Off Accrued")
#     medical_insurance_cost = fields.Integer(string="Medical insurance cost")
#
#     employee_gosi_saudi = fields.Float(string="Employee Gosi (Saudi)")
#     net_salary = fields.Float(string="Net Salary")
#
#     vacation_premium = fields.Float(string="Vacation Premium",)
#     eos_premium = fields.Float(string="EOS Premium", )
#     ticket_premium = fields.Float(string="Ticket Premium",)
#     iqama_renew_premium = fields.Float(string="Iqama Renew Premium")
#     medical_insurance = fields.Float(string="Medical Insurance")
#     gosi_company_share = fields.Float(string="Gosi Company Share")
#     total_unpaid = fields.Float(string="Total Unpaid",)
#     total_monthly_cost = fields.Float(string="Total Monthly Cost",)
#
#     children = fields.Integer(string='Number of Followers',)
#
#     unpaid_house_amount = fields.Float(string="Unpaid House Amount",)
#     unpaid_transportation_amount = fields.Float(string="Unpaid Transportation Amount",
#                                                    )
#     unpaid_other_allowances = fields.Float(string="Unpaid Other Allowances", )
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def mail_reminder(self):
        """Sending expiry date notification for ID and Passport"""

        now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([])
        iqama_group = self.env.ref('pt_hr_employee_updation.iqama_group_notification')  # Example: 'base.group_user' for internal users
        users_in_group = self.env['res.users'].search([
            ('groups_id', 'in', iqama_group.id)
        ])
        passport_group = self.env.ref(
            'pt_hr_employee_updation.passport_group_notification')  # Example: 'base.group_user' for internal users
        users_in_group_passport = self.env['res.users'].search([
            ('groups_id', 'in', passport_group.id)
        ])
        for i in match:
            if i.id_expiry_date_new:
                exp_date = fields.Date.from_string(i.id_expiry_date_new) - timedelta(days=14)
                exp_date2 = fields.Date.from_string(i.id_expiry_date_new) - timedelta(days=i.company_id.iqama_notification_day_number)
                if date_now >= exp_date:
                    mail_content = "  Hello  " + i.name + ",<br>Your ID " + i.identification_id + "is going to expire on " + \
                                   str(i.id_expiry_date_new) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('ID-%s Expired On %s') % (i.identification_id, i.id_expiry_date_new),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
                if date_now >= exp_date2:
                    note = _("Please Review Iqama will Expire")
                    summary = _("  Hello  " + i.name + "Your ID " + i.identification_id + "is going to expire on " + \
                                   str(i.id_expiry_date_new) + ". Please renew it before expiry date")
                    for user in users_in_group:
                        i.sudo().activity_schedule(
                            'mail.mail_activity_data_todo', fields.Date.today(),
                            note=note,
                            user_id=user.id,
                            res_id=i.id,
                            summary=summary
                        )
            if i.passport_expiry_date:
                exp_date1 = fields.Date.from_string(i.passport_expiry_date) - timedelta(days=180)
                expr_date2 = fields.Date.from_string(i.passport_expiry_date) - timedelta(
                    days=i.company_id.passport_notification_day_number)
                if date_now >= exp_date1:
                    mail_content = "  Hello  " + i.name + ",<br>Your Passport " + i.passport_id + "is going to expire on " + \
                                   str(i.passport_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('Passport-%s Expired On %s') % (i.passport_id, i.passport_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
                if date_now >= expr_date2:
                    note = _("Please Review Passport will Expire")
                    summary = _(
                        "  Hello  " + i.name + "Your Passport " + i.passport_id + "is going to expire on " + \
                        str(i.passport_expiry_date) + ". Please renew it before expiry date")
                    for user in users_in_group_passport:
                        i.sudo().activity_schedule(
                            'mail.mail_activity_data_todo', fields.Date.today(),
                            note=note,
                            user_id=user.id,
                            res_id=i.id,
                            summary=summary
                        )
            if i.balady_date:
                exp_date1 = fields.Date.from_string(i.balady_date) - timedelta(
                    days=i.company_id.balady_notification_day_number)
                if date_now >= exp_date1:
                    balady_group = self.env.ref(
                        'pt_hr_employee_updation.balady_group_notification')  # Example: 'base.group_user' for internal users
                    users_in_group_balady = self.env['res.users'].search([
                        ('groups_id', 'in', balady_group.id)
                    ])
                    note = _("Please Review Balady will Expire")
                    summary = _(
                        "  Hello  " + i.name + "Your Balady " + i.balady_card_num + "is going to expire on " + \
                        str(i.balady_date) + ". Please renew it before expiry date")
                    for user in users_in_group_balady:
                        i.sudo().activity_schedule(
                            'mail.mail_activity_data_todo', fields.Date.today(),
                            note=note,
                            user_id=user.id,
                            res_id=i.id,
                            summary=summary
                        )

    joining_date = fields.Date(string='Joining Date', help="Employee joining date computed from the contract start date",compute='compute_joining', store=True)
    id_expiry_date = fields.Date(string='ID Expiry Date', help='Expiry date of Identification ID')
    id_expiry_date_new = fields.Date(string='Expiry Date Identification ID', help='Expiry date of Identification ID')
    passport_expiry_date = fields.Date(string='Passport Expiry Date', help='Expiry date of Passport ID')
    id_attachment_id = fields.Many2many('ir.attachment', 'id_attachment_rel', 'id_ref', 'attach_ref',
                                        string="ID Attachment", help='You can attach the copy of your Id')
    passport_attachment_id = fields.Many2many('ir.attachment', 'passport_attachment_rel', 'passport_ref', 'attach_ref1',
                                              string="Passport Attachment",
                                              help='You can attach the copy of Passport')
    fam_ids = fields.One2many('hr.employee.family', 'employee_id', string='Family', help='Family Information')
    passport_name_ar = fields.Char(string='Passport Arabic Name')
    passport_name_en = fields.Char(string='English Name')
    issue_date = fields.Date(string='Issue Date',)
    passport_issuer = fields.Char(string='Issue Place')
    passport_Type = fields.Char(string='Passport Type')
    enlistment_status = fields.Char(string='Enlistment Status')
    job_position = fields.Many2one('hr.job', string="Job in Passport",)
    passport_address = fields.Char(string='Passport Address')
    passport_national_no = fields.Char(string='National No.')
    is_passport = fields.Boolean(string='Passport?',)

    border_number = fields.Char(string="Border Number", )
    expiry_border_number_date = fields.Date(string='Entry Date', help='Entry date of Border Number')
    religion = fields.Selection(
        [('mus', 'Muslem'),('non_mus', 'Non Muslem')],
        string="Religion")

    @api.depends('contract_id')
    def compute_joining(self):
        if self.contract_id:
            date = min(self.contract_id.mapped('date_start'))
            self.joining_date = date
        else:
            self.joining_date = False

    @api.onchange('spouse_complete_name', 'spouse_birthdate')
    def onchange_spouse(self):
        relation = self.env.ref('pt_hr_employee_updation.employee_relationship')
        lines_info = []
        spouse_name = self.spouse_complete_name
        date = self.spouse_birthdate
        if spouse_name and date:
            lines_info.append((0, 0, {
                'member_name': spouse_name,
                'relation_id': relation.id,
                'birth_date': date,
            })
                              )
            self.fam_ids = [(6, 0, 0)] + lines_info


class EmployeeRelationInfo(models.Model):
    """Table for keep employee family information"""

    _name = 'hr.employee.relation'
    _description = 'Employee Relation'

    name = fields.Char(string="Relationship", help="Relationship with thw employee")

class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    is_editable = fields.Boolean("Expense Lines Are Editable By Current User", compute='_compute_is_editable')

    @api.depends_context('uid')
    @api.depends('employee_id', 'user_id', 'state')
    def _compute_is_editable(self):
        is_manager = self.env.user.has_group('hr_expense.group_hr_expense_manager')
        is_approver = self.env.user.has_group('hr_expense.group_hr_expense_user')
        for report in self:
            # Employee can edit his own expense in draft only
            # is_editable = (is_manager and report.state in ['draft', 'submit', 'approve'])
            report.is_editable = False
            if is_manager or is_approver:
                report.is_editable = True

    @api.depends('employee_id')
    def _compute_can_reset(self):
        is_expense_user = self.env.user.has_group('hr_expense.group_hr_expense_team_approver')
        for sheet in self:
            sheet.can_reset = False
            if is_expense_user:
                sheet.can_reset = True

    @api.depends_context('uid')
    @api.depends('employee_id')
    def _compute_can_approve(self):
        is_approver = self.env.user.has_group('hr_expense.group_hr_expense_team_approver, hr_expense.group_hr_expense_user')
        is_manager = self.env.user.has_group('hr_expense.group_hr_expense_manager')
        for sheet in self:
            sheet.can_approve = False
            if is_manager or is_approver:
                sheet.can_approve = True
