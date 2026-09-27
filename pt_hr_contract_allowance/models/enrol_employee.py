from odoo import models, fields, api, _


class EnrolEmployee(models.Model):
    _name = 'enrol.employee'

    name = fields.Char()
    # cr = fields.Integer()
    # wol = fields.Integer()
    cr = fields.Char()
    wol = fields.Char()







