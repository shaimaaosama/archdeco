
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GsDrivingLicenseRestriction(models.Model):
    _name = 'gs.driving.license.restriction'
    _description = 'Driving License Restriction'

    name = fields.Char(string='Name',)