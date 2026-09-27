# -*- coding: utf-8 -*-

from odoo import models, fields


class GSTask(models.Model):
    _name = 'gs.task'
    _description = 'Task'

    name = fields.Char(string='Name',)