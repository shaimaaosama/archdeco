# -*- coding: utf-8 -*-
# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class Allowances(models.Model):
    _name = 'hr.allowance'
    _description = 'Allowances'

    name = fields.Char('Allowance')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.action_create_allowances_collect()
        return records

    def action_create_allowances_collect(self):
        for rec in self:
            self.env["allowances.collect"].create({"name": rec.name})