# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError


class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    payment_term_ids = fields.Many2many('account.payment.term', 'payment_term_ids01', 'payment_term_ids001',
                                        'payment_term_ids0001', string='Payment Terms',)

