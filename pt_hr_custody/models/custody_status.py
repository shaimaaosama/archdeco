# -*- coding: utf-8 -*-

from odoo import models, fields


class HrCustodyStatus(models.Model):
    _name = 'hr.custody.status'
    _description = 'HR Custody Status'

    name = fields.Char(string="Name")
