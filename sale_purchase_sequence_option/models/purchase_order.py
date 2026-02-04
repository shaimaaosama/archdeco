# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _

class IrSequenceOption(models.Model):
    _inherit = "ir.sequence.option"

    model = fields.Selection(
        selection_add=[("purchase.order", "purchase.order")],
        ondelete={"purchase.order": "cascade"},
    )

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.model
    def create(self, vals):
        seq = self.env["ir.sequence.option.line"].get_sequence(self.new(vals))
        self = self.with_context(sequence_option_id=seq.id)
        res = super().create(vals)
        return res

    def action_create_invoice(self):
        res = super().action_create_invoice()
        if self.invoice_ids:
            for invoice in self.invoice_ids:
                if invoice.invoice_line_ids:
                    for line in invoice.invoice_line_ids:
                        if line.purchase_line_id:
                            line.discount = line.purchase_line_id.discount
        return res