# -*- coding: utf-8 -*-

from odoo import models, fields


class GsBailTypeLevel(models.Model):
    _name = 'gs.bail.type'
    _description = 'Bail type'

    name = fields.Char(string='Name',)