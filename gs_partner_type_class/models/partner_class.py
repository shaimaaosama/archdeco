# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GsPartnerClass(models.Model):
    _name = 'gs.partner.class'
    _description = 'Partner Clas'

    name = fields.Char(string='Name')
