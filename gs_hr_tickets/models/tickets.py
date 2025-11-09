# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GsTickets(models.Model):
    _name = 'gs.tickets'
    _description = 'Tickets'

    contract_id = fields.Many2one('hr.contract')
    country_id = fields.Many2one('res.country', 'Nationality', tracking=True)
    economy_fare = fields.Integer(string='Economy Fare', )
    business_class_fare = fields.Integer(string='Business Class Fare', )