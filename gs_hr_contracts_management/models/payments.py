# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GsPayments(models.Model):
    _name = 'gs.payments'
    _description = 'Payments'

    name = fields.Char()
    percentage = fields.Float(string="Percentage")
