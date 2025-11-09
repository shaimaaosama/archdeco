# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GsSubject(models.Model):
    _name = 'gs.subject'
    _description = 'Subject'

    name = fields.Char()
    partner_id = fields.Many2one('res.partner', string='Partner')
    num_page = fields.Char(string="Number Of Pages")
    description = fields.Text(string="Description")
    bol_active = fields.Boolean(tracking=True, string="Active")
    attachment_ids = fields.Many2many('ir.attachment', 'subject_attachment_rel', 'subject_template_id',
                                      'subject_attachment_id', 'Attachments', tracking=True, )
    
    payment_count = fields.Integer(compute='get_gs_payment_count')

    def open_gs_payment(self):
        return {
            'name': _('Contract Payment'),
            'domain': [('book_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'gs.contact.payment.schedule',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_gs_payment_count(self):
        count = self.env['gs.contact.payment.schedule'].search_count([('book_id', '=', self.id)])
        self.payment_count = count