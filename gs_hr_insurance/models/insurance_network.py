# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GsInsuranceNetwork(models.Model):
    _name = 'gs.insurance.network'

    name = fields.Char(string='Name', )
    contract_id = fields.Many2one('gs.insurance.contract',string='Contract',)
    insurance_class_ids = fields.Many2one('gs.insurance.class', string="Insurance Class")
    id_attachment_id = fields.Many2many('ir.attachment', 'id_attachment_id03', 'id_attachment_id003', 'id_attachment_id0003',
                                        string="Attachment", help='Attachment of Network')