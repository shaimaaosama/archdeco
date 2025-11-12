# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GsResidenceProfession(models.Model):
    _name = 'gs.residence.profession'
    _description = 'Residence Profession'

    name = fields.Char(string='Name',)