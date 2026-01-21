from odoo import models, api


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        res = super().action_post()

        # Read the auto reconcile method configuration
        param = self.env["ir.config_parameter"].sudo()
        method = param.get_param("auto_reconcile_config.method", False)  

        # Only run auto reconcile if a method is configured
        if method:
            for pay in self:
                if pay.payment_type == "inbound":
                    pay.auto_reconcile_invoices()

        return res

    def auto_reconcile_invoices(self):
        """Auto reconcile payment with invoices using FIFO/LIFO/SAME logic."""

        for pay in self:

            # Only inbound customer payments
            if pay.payment_type != "inbound":
                continue

            partner = pay.partner_id
            company = pay.company_id

           
            param = self.env["ir.config_parameter"].sudo()
            method = param.get_param("auto_reconcile_config.method", "fifo")
            
            invoices = self.env["account.move"].search([
                ("partner_id", "=", partner.id),
                ("company_id", "=", company.id),
                ("state", "=", "posted"),
                ("move_type", "in", ("out_invoice", "out_refund")),
                ("payment_state", "!=", "paid"),
            ])

            # Filter only invoices with receivable residual
            invoices = invoices.filtered(lambda inv: any(
                l.account_id.account_type == "asset_receivable"
                and abs(l.amount_residual) > 0
                for l in inv.line_ids
            ))

            
            if not invoices:
                continue

            
            if method == "fifo":
                invoices = invoices.sorted(key=lambda inv: (inv.invoice_date or inv.date, inv.id))

            elif method == "latest":
                invoices = invoices.sorted(
                    key=lambda inv: (inv.invoice_date or inv.date, inv.id),
                    reverse=True,
                )

            elif method == "same":
                invoices = invoices.filtered(
                    lambda inv: abs(inv.amount_residual - pay.amount) < 0.00001
                ).sorted(key=lambda inv: inv.id)

            
            if not invoices:
                continue

            
            pay_line = pay.move_id.line_ids.filtered(
                lambda l: l.account_id.account_type == "asset_receivable"
                and abs(l.amount_residual) > 0
            )

            
            if not pay_line:
                continue

            
            for inv in invoices:

                
                if abs(pay_line.amount_residual) <= 0.00001:
                    break

                inv_line = inv.line_ids.filtered(
                    lambda l: l.account_id.account_type == "asset_receivable"
                    and abs(l.amount_residual) > 0
                )

                if not inv_line:
                    continue

                
                (inv_line | pay_line).with_context(no_exchange_diff=True).reconcile()

                pay.message_post(body=f"Auto-reconciled with Invoice {inv.name}")

            
            if abs(pay_line.amount_residual) <= 0.00001:
                pay.state = "paid"
            else:
                pay.state = "in_process"

            
            pay._compute_stat_buttons_from_reconciliation()
            pay.flush_recordset()
            pay.invalidate_recordset([
                "reconciled_invoice_ids",
                "reconciled_invoices_count",
                "reconciled_invoices_type",
                "reconciled_bill_ids",
                "reconciled_bills_count",
                "reconciled_statement_line_ids",
                "reconciled_statement_lines_count",
            ])

