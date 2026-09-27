from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class SaleOderInherit(models.Model):
    _inherit = 'sale.order'

    entry_status = fields.Selection([
        ('cancelled', 'Cancelled Order'),
        ('not_billed', 'Not Invoiced'),
        ('posted_bill', 'Posted Invoice'),
        ('partially_posted', 'Partially Posted'),
        ('not_posted', 'Not Posted')
    ], compute="_compute_entry_status", store=True)

    @api.depends(
        'order_line.invoice_lines.move_id.state',
        'order_line.invoice_lines.move_id.move_type',
        'state'
    )
    def _compute_entry_status(self):
        for order in self:
            if order.state == 'cancel':
                order.entry_status = 'cancelled'
            else:
                invoices = order.invoice_ids
                if not invoices:
                    order.entry_status = 'not_billed'
                    continue

                invoices = invoices.filtered(lambda m: m.state != 'cancel')

                if not invoices:
                    order.entry_status = 'not_billed'
                    continue

                posted_bills = invoices.filtered(lambda m: m.state == 'posted')

                if len(posted_bills) == len(invoices):
                    order.entry_status = 'posted_bill'
                elif len(posted_bills) == 0:
                    order.entry_status = 'not_posted'
                else:
                    order.entry_status = 'partially_posted'

    approval_count = fields.Integer(
        string="Approvals",
        compute="_compute_approval_count",
    )

    def _compute_approval_count(self):
        for order in self:
            order.approval_count = self.env['approval.request'].search_count([("sale_order_id", "=", order.id),])


    def action_view_approvals(self):
        self.ensure_one()

        return {
            "name": _("Approvals"),
            "type": "ir.actions.act_window",
            "res_model": "approval.request",
            "view_mode": "list,form",
            "view_id": False,
            "domain": [
                ("sale_order_id", "=", self.id),
            ],
            "context": {
                "create": False,
                "edit": False,
                "delete": False,
            },
        }