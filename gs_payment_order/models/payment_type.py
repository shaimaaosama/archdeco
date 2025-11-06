# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GsPaymentType(models.Model):
    _name = 'gs.payment.type'
    _description = 'Payment Type'

    name = fields.Char()
    finalize_payment_user_ids = fields.Many2many("res.users",'user_id2','user_id22','user_id222', string="Finalize Payment Users")