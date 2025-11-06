# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SpecialApprovalButtonWizard(models.TransientModel):
    _name = 'gs.special.approval.button.wizard'

    user_ids = fields.Many2many('res.users', string="Users")

    def create_special_approval(self):
        active_id = self._context.get('active_ids') or self._context.get('active_id')
        purchase_tracking = self.env['gs.payment.order'].search([('id', '=', active_id)])
        purchase_tracking.action_crate_special_approval(self.user_ids)