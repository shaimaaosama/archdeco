from odoo import fields, models, api, _


class StockLandedCostInherit(models.Model):
    _inherit = 'stock.landed.cost'

    def button_validate(self):
        res = super().button_validate()

        ctx = {
            "check_move_validity": False,
            "skip_account_move_synchronization": True,
            "skip_invoice_sync": True,
            "skip_invoice_line_sync": True,
            "skip_move_branch_default": True,
        }

        for rec in self:
            move = rec.account_move_id
            if not move:
                continue

            for cost_line in rec.cost_lines.filtered(lambda l: l.partner_id and l.name):
                cost_name = (cost_line.name or "").strip().lower()
                if not cost_name:
                    continue

                move_lines = move.line_ids.filtered(
                    lambda ml:
                    cost_name in ((ml.name or "").lower())
                    and not ml.partner_id
                )

                if move_lines:
                    move_lines.sudo().with_context(**ctx).write({
                        "partner_id": cost_line.partner_id.id,
                    })

        return res


class StockLandedCostLineInherit(models.Model):
    _inherit = 'stock.landed.cost.lines'

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        tracking=True,
    )