# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class InheritEmployee(models.Model):
    _inherit = 'hr.employee'

    discipline_count = fields.Integer(compute="_compute_discipline_count")
    disciplinary_action_ids = fields.One2many('disciplinary.action', 'employee_name')

    def _compute_discipline_count(self):
        all_actions = self.env['disciplinary.action'].read_group([
            ('employee_name', 'in', self.ids),
            ('state', '=', 'action'),
        ], fields=['employee_name'], groupby=['employee_name'])
        mapping = dict([(action['employee_name'][0], action['employee_name_count']) for action in all_actions])
        for employee in self:
            employee.discipline_count = mapping.get(employee.id, 0)


class CategoryDiscipline(models.Model):
    _name = 'discipline.category'
    _description = 'Reason Category'

    # Discipline Categories

    code = fields.Char(string="Code", required=True, help="Category code")
    name = fields.Char(string="Name", required=True, help="Category name")
    category_type = fields.Selection([('disciplinary', 'Disciplinary Category'), ('action', 'Action Category')],
                                     string="Category Type", help="Choose the category type disciplinary or action")
    description = fields.Text(string="Details", help="Details for this category")
    employee_name = fields.Many2one('hr.employee', string='Employee', required=False, help="Employee name")
    category_line_ids = fields.One2many('category.line', 'discipline_category_id')
    fixed_amount = fields.Float('No Of Days')


class CategoryLine(models.Model):
    _name = 'category.line'
    _description = 'Category Line'

    num = fields.Integer()
    discipline_category_id = fields.Many2one('discipline.category')
    discipline_action_id = fields.Many2one('discipline.category', domain="[('category_type', '=', 'action')]")


class DisciplinaryAction(models.Model):
    _name = 'disciplinary.action'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Disciplinary Action"

    state = fields.Selection([('draft', 'Draft'), ('explain', 'Waiting Explanation'), ('submitted', 'Waiting Action'),
                              ('action', 'Action Validated'),
                              ('cancel', 'Cancelled')], default='draft', tracking=True)

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True,
                       default='New')

    employee_name = fields.Many2one('hr.employee', string='Employee', required=True, help="Employee name")
    department_name = fields.Many2one('hr.department', string='Department', required=True, help="Department name")
    discipline_reason = fields.Many2one('discipline.category', string='Reason', required=True,
                                        help="Choose a disciplinary reason")
    num_reason = fields.Integer(string='Num Of Reason', compute='_compute_num_reason')
    explanation = fields.Text(string="Explanation by Employee", help='Employee have to give Explanation'
                                                                     'to manager about the violation of discipline')
    action = fields.Many2one('discipline.category', string="Action",
                             help="Choose an action for this disciplinary action")
    category_line_id = fields.Many2one('discipline.category', string='Penalties')
    amount = fields.Float(string='Fixed Amount', related='category_line_id.fixed_amount',readonly=False,store=True)
    read_only = fields.Boolean(compute="get_user", default=True)
    warning_letter = fields.Html(string="Warning Letter")
    suspension_letter = fields.Html(string="Suspension Letter")
    termination_letter = fields.Html(string="Termination Letter")
    warning = fields.Boolean(default=False)
    action_details = fields.Text(string="Action Details", help="Give the details for this action")
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments",
                                      help="Employee can submit any documents which supports their explanation")
    note = fields.Text(string="Internal Note")
    joined_date = fields.Date(string="Joined Date", help="Employee joining date")
    applied_date = fields.Date(string='Applied Date')
    role_by = fields.Selection(
        [('fixed', 'Fixed'), ('percentage', 'Percentage'), ('time', 'Time By Hours'), ('days', 'Days')], 'Role By',
        tracking=True, default='days')
    by_percentage_type = fields.Selection([('wage', 'Wage'), ('gross', 'Gross'), ('net', 'Net')], 'Percentage By',
                                          tracking=True)
    percentage = fields.Float('Percentage', tracking=True)

    # assigning the sequence for the record
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('disciplinary.action')
        return super(DisciplinaryAction, self).create(vals_list)

    # Check the user is a manager or employee
    @api.depends('read_only')
    def get_user(self):

        if self.env.user.has_group('hr.group_hr_manager'):
            self.read_only = True
        else:
            self.read_only = False

    # Check the Action Selected

    @api.onchange('employee_name')
    def onchange_employee_name(self):

        department = self.env['hr.employee'].search([('name', '=', self.employee_name.name)])
        self.department_name = department.department_id.id

        if self.state == 'action':
            raise ValidationError(_('You Can not edit a Validated Action !!'))

    @api.onchange('discipline_reason')
    def onchange_reason(self):
        if self.state == 'action':
            raise ValidationError(_('You Can not edit a Validated Action !!'))

    def assign_function(self):

        for rec in self:
            rec.state = 'explain'

    def cancel_function(self):
        for rec in self:
            rec.state = 'cancel'

    def set_to_function(self):
        for rec in self:
            rec.state = 'draft'

    def action_function(self):
        for rec in self:
            # if not rec.action_details or rec.action_details == '<p><br></p>':
            #     raise ValidationError(_('You have to fill up the Action Details in Action Information !!'))
            rec.state = 'action'

    def explanation_function(self):
        for rec in self:

            if not rec.explanation:
                raise ValidationError(_('You must give an explanation !!'))

        self.write({
            'state': 'submitted'
        })

    @api.depends('num_reason')
    def _compute_num_reason(self):
        """ Compute num_reason value """
        for rec in self:
            rec.num_reason = len(rec.employee_name.disciplinary_action_ids.filtered(
                lambda l: l.discipline_reason.id == rec.discipline_reason.id))

    @api.constrains('discipline_reason')
    def _check_discipline_reason(self):
        """ Validate discipline_reason """
        for rec in self:
            for line in rec.discipline_reason.category_line_ids:
                if rec.num_reason == line.num:
                    rec.action = line.discipline_action_id.id
                    rec.category_line_id = line.discipline_action_id.id
