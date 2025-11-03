# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReceiptButtonWizard(models.TransientModel):
    _name = 'gs.receipt.button.wizard'

    scheduled_date = fields.Datetime('Scheduled Date')

    def create_receipt(self):
        active_id = self._context.get('active_ids') or self._context.get('active_id')
        purchase_tracking = self.env['gs.purchase.tracking'].search([('id', '=', active_id)])
        purchase_tracking.action_crate_receipt(self.scheduled_date)