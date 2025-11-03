# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools.misc import format_date, DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta


class CrmLeadInherit(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def create(self, vals):
        if vals.get('sequence', _('New')) == _('New'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code('gs.crm.sequence') or _('New')
        result = super(CrmLeadInherit, self).create(vals)
        return result

    project_id = fields.Many2one("project.project", string="Project")
    project_state = fields.Char(string='Project State')
    pr_city = fields.Char(string='City')
    owner = fields.Char(string='Owner')
    main_contractor = fields.Char(string='Main Contractor')
    consultant = fields.Char(string='Consultant')
    ent_req_pricing = fields.Char(string='Entity Requesting Pricing')
    contact = fields.Char(string='Contact')
    contact_number = fields.Char(string='Contact Number')
    crm_line_ids = fields.One2many(comodel_name='crm.lead.line', inverse_name='link_id',)
    crm_attachment_ids = fields.One2many(comodel_name='crm.attachment.line', inverse_name='link_id',)
    crm_more_inf_ids = fields.One2many(comodel_name='crm.more.inf.line', inverse_name='link_id',)
    crm_project_inf_ids = fields.One2many(comodel_name='crm.project.inf.line', inverse_name='link_id',)
    sequence = fields.Char(string='Sequence')

    @api.onchange('name')
    def _onchange_name01(self):
        if not self.crm_attachment_ids:
            at_01 = [{
                'attachment': "جدول الكميات",
            }]
            at_02 = [{
                'attachment': "جدول المواصفات",

            }]
            at_03 = [{
                'attachment': "المخططات التنفيذية",

            }]
            at_04 = [{
                'attachment': "مرفقات إضافية",

            }]
            line_ids = at_01 + at_02 + at_03 + at_04

            self.crm_attachment_ids = [(0, 0, x) for x in line_ids]

        if not self.crm_more_inf_ids:
            mo_01 = [{
                'name': "طلب معلومات اضافية",
            }]
            mo_02 = [{
                'name': "قبول التسعير",

            }]
            mo_03 = [{
                'name': "الاعتذار عن التسعير",

            }]

            mo_line_ids = mo_01 + mo_02 + mo_03

            self.crm_more_inf_ids = [(0, 0, x) for x in mo_line_ids]

        if not self.crm_project_inf_ids:
            mo_01 = [{
                'name': "طلب معلومات اضافية",
            }]
            mo_02 = [{
                'name': "قبول التسعير",

            }]
            mo_03 = [{
                'name': "الاعتذار عن التسعير",

            }]

            mo_line_ids = mo_01 + mo_02 + mo_03

            self.crm_project_inf_ids = [(0, 0, x) for x in mo_line_ids]


class CrmLeadLine(models.Model):
    _name = 'crm.lead.line'

    link_id = fields.Many2one("crm.lead")
    item_required_for_pricing = fields.Char(string='Items Required For Pricing')
    notes = fields.Char(string='Notes')


class CrmAttachmentLine(models.Model):
    _name = 'crm.attachment.line'

    link_id = fields.Many2one("crm.lead")
    attachment = fields.Char(string='Attachment')
    notes = fields.Char(string='Notes')


class CrmMoreInfLine(models.Model):
    _name = 'crm.more.inf.line'

    link_id = fields.Many2one("crm.lead")
    bol = fields.Boolean(string=' ')
    name = fields.Char(string='Name')
    notes = fields.Char(string='Notes')


class ProjectInfLine(models.Model):
    _name = 'crm.project.inf.line'

    link_id = fields.Many2one("crm.lead")
    bol = fields.Boolean(string=' ')
    name = fields.Char(string='Name')
    notes = fields.Char(string='Notes')

