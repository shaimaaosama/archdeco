# -*- coding: utf-8 -*-
from odoo import models, api, _

class AccountMove(models.Model):
    _inherit = "account.move"

    def _generate_deferred_entries(self):
        """
        Generates the deferred entries for the invoice, with support for per-product accounts.
        """
        # We need to mostly copy the original method logic but move account selection inside the loop.
        self.ensure_one()
        if self.state != 'posted':
            return
        # The original method has safety checks, we should keep them or call super if possible.
        # But since we need to change variables used deep inside the logic, 
        # a full override is often necessary in Odoo for this kind of core logic change.
        
        # We will follow the same logic as the original but with per-line account selection.
        from odoo import Command
        from itertools import chain
        from odoo.exceptions import UserError

        if self.is_entry():
            raise UserError(_("You cannot generate deferred entries for a miscellaneous journal entry."))
            
        deferred_type = "expense" if self.is_purchase_document() else "revenue"
        deferred_journal = self.company_id.deferred_expense_journal_id if deferred_type == "expense" else self.company_id.deferred_revenue_journal_id
        
        if not deferred_journal:
            raise UserError(_("Please set the deferred journal in the accounting settings."))

        moves_vals_to_create = []
        lines_vals_to_create = []
        lines_periods = []
        
        for line in self.line_ids.filtered(lambda l: l.deferred_start_date and l.deferred_end_date):
            product = line.product_id
            
            # 1. Determine Deferred Account (Asset/Liability)
            line_deferred_account = False
            if deferred_type == 'expense':
                line_deferred_account = product.property_account_deferred_expense_id
            else:
                line_deferred_account = product.property_account_deferred_revenue_id
                
            if not line_deferred_account:
                 raise UserError(_("Please set the deferred accounts in the accounting settings or on the product %s.", product.display_name))

            # 2. Determine P&L Account
            line_pnl_account = line.account_id # Default to invoice line account
            # if deferred_type == 'expense' and product.property_account_deferred_expense_pnl_id:
            #     line_pnl_account = product.property_account_deferred_expense_pnl_id
            # elif deferred_type == 'revenue' and product.property_account_deferred_revenue_pnl_id:
            #     line_pnl_account = product.property_account_deferred_revenue_pnl_id

            periods = line._get_deferred_periods()
            if not periods:
                continue

            ref = _("Deferral of %s", line.move_id.name or '')

            moves_vals_to_create.append({
                'move_type': 'entry',
                'deferred_original_move_ids': [Command.set(line.move_id.ids)],
                'journal_id': deferred_journal.id,
                'company_id': self.company_id.id,
                'partner_id': line.partner_id.id,
                'auto_post': 'at_date',
                'ref': ref,
                'name': False,
                'date': line.move_id.date,
            })
            
            # The "Fully Deferred" move lines:
            # Reverses the original expense/revenue and puts it into deferred account
            lines_vals_to_create.append([
                self.env['account.move.line']._get_deferred_lines_values(account.id, coeff * line.balance, ref, line.analytic_distribution, line)
                for (account, coeff) in [(line.account_id, -1), (line_deferred_account, 1)]
            ])
            lines_periods.append((line, periods, line_deferred_account, line_pnl_account))

        if not moves_vals_to_create:
            return

        # Create the fully deferred moves
        moves_fully_deferred = self.create(moves_vals_to_create)
        for move_fully_deferred, lines_vals in zip(moves_fully_deferred, lines_vals_to_create):
            for line_vals in lines_vals:
                line_vals['move_id'] = move_fully_deferred.id
        self.env['account.move.line'].create(list(chain(*lines_vals_to_create)))

        deferral_moves_vals = []
        deferral_moves_line_vals = []
        
        # Create the periodic deferral entries
        for (line, periods, line_deferred_account, line_pnl_account), move_vals in zip(lines_periods, moves_vals_to_create):
            remaining_balance = line.balance
            for period_index, period in enumerate(periods):
                force_balance = remaining_balance if period_index == len(periods) - 1 else None
                deferred_amounts = self._get_deferred_amounts_by_line(line, [period], deferred_type)[0]
                balance = deferred_amounts[period] if force_balance is None else force_balance
                remaining_balance -= line.currency_id.round(balance)
                
                deferral_moves_vals.append({**move_vals, 'date': period[1]})
                
                # The periodic move lines:
                # Moves from deferred account back to P&L account
                deferral_moves_line_vals.append([
                    {
                        **self.env['account.move.line']._get_deferred_lines_values(account.id, coeff * balance, move_vals['ref'], line.analytic_distribution, line),
                        'partner_id': line.partner_id.id,
                        'product_id': line.product_id.id,
                    }
                    # Note: Original code used deferred_amounts['account_id'], 
                    # which we want to override with line_pnl_account.
                    for (account, coeff) in [(line_pnl_account, 1), (line_deferred_account, -1)]
                ])

        deferral_moves = self.create(deferral_moves_vals)
        for deferral_move, lines_vals in zip(deferral_moves, deferral_moves_line_vals):
            for line_vals in lines_vals:
                line_vals['move_id'] = deferral_move.id
        self.env['account.move.line'].create(list(chain(*deferral_moves_line_vals)))

        # Rounding and cleanup logic (same as original)
        to_unlink = deferral_moves.filtered(lambda move: move.currency_id.is_zero(move.amount_total))
        for move_fully_deferred in moves_fully_deferred:
            deferred_move_ids = move_fully_deferred + deferral_moves
            cancelling_moves = deferred_move_ids.filtered(lambda move:
                move_fully_deferred.date.replace(day=1) == move.date.replace(day=1)
                and move.amount_total == move_fully_deferred.amount_total
            )
            if len(cancelling_moves) == 2:
                to_unlink |= cancelling_moves
                continue

        to_unlink.unlink()
        (moves_fully_deferred + deferral_moves - to_unlink)._post(soft=True)
