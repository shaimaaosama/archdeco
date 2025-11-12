# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GsTypeOfMembership(models.Model):
    _name = 'gs.type.of.membership'
    _description = 'Type Of Membership'

    name = fields.Char(string='Name',)