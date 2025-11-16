from odoo import _, api, fields, models


class Reason(models.Model):
    _name = 'gs.reason'

    name = fields.Char(string='Name')