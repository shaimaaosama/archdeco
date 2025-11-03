# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GsOption(models.Model):
    _name = 'gs.option'
    _description = 'Option'

    name = fields.Char(string='Name')
