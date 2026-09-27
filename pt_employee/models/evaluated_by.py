# -*- coding: utf-8 -*-

from odoo import models, fields


class GSEvaluatedBy(models.Model):
    _name = 'gs.evaluated.by'
    _description = 'Evaluated By'

    name = fields.Char(string='Name',)