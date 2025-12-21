# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _

class IrSequenceOption(models.Model):
    _inherit = "ir.sequence.option"

    model = fields.Selection(
        selection_add=[("sale.order", "sale.order")],
        ondelete={"sale.order": "cascade"},
    )

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def create(self, vals):
        seq = self.env["ir.sequence.option.line"].get_sequence(self.new(vals))
        self = self.with_context(sequence_option_id=seq.id)
        res = super().create(vals)
        return res