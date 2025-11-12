# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GsTypeOfLicense(models.Model):
    _name = 'gs.type.of.license'
    _description = 'Type Of License'

    name = fields.Char(string='Name',)