# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GsPartnerType(models.Model):
    _name = 'gs.partner.type'
    _description = 'Partner Type'

    name = fields.Char(string='Name')
    user_id = fields.Many2many("res.users", "user_id_gpt01", "user_id_gpt001", "user_id_gpt0001", string="Users")

