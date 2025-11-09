# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GsRemind(models.Model):
    _name = 'gs.remind'
    _description = 'Reminders'

    name = fields.Char()