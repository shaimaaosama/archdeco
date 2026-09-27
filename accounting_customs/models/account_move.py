from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_is_zero
import uuid
import re


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    def _get_safe_analytic_ids_from_distribution(self, analytic_distribution):
        analytic_ids = []
        for analytic_key in (analytic_distribution or {}).keys():
            for part in str(analytic_key).split(','):
                part = part.strip()
                if part.isdigit():
                    analytic_ids.append(int(part))
        return list(set(analytic_ids))

    def _get_safe_analytic_items_from_distribution(self, analytic_distribution):
        items = []
        for analytic_key, percentage in (analytic_distribution or {}).items():
            for part in str(analytic_key).split(','):
                part = part.strip()
                if part.isdigit():
                    items.append((int(part), percentage or 0.0))
        return items

    def _get_landed_cost_record(self):
        self.ensure_one()
        return self.env["stock.landed.cost"].search([
            ("account_move_id", "=", self.id)
        ], limit=1)

    def _is_landed_cost_move(self):
        self.ensure_one()
        return bool(self._get_landed_cost_record())

    def _fix_amount_currency_sign(self, line, debit, credit, amount_currency):
        debit = debit or 0.0
        credit = credit or 0.0
        amount_currency = amount_currency or 0.0
        balance = debit - credit

        company_currency = line.company_id.currency_id
        line_currency = line.currency_id or company_currency

        if line_currency == company_currency:
            return balance

        if debit > 0:
            return abs(amount_currency) or abs(balance)

        if credit > 0:
            return -(abs(amount_currency) or abs(balance))

        return 0.0

    def _sanitize_landed_cost_amount_currency(self):
        ctx = {
            "check_move_validity": False,
            "skip_account_move_synchronization": True,
            "skip_invoice_sync": True,
            "skip_invoice_line_sync": True,
            "skip_move_branch_default": True,
        }

        for move in self:
            if move.state != "draft":
                continue

            if not move._is_landed_cost_move():
                continue

            company_currency = move.company_id.currency_id

            for line in move.line_ids:
                if line.display_type not in (False, "product", "cogs"):
                    continue

                debit = line.debit or 0.0
                credit = line.credit or 0.0
                balance = debit - credit
                currency = line.currency_id or company_currency
                amount_currency = line.amount_currency or 0.0

                if currency == company_currency:
                    new_amount_currency = balance
                elif debit > 0:
                    new_amount_currency = abs(amount_currency) or abs(balance)
                elif credit > 0:
                    new_amount_currency = -(abs(amount_currency) or abs(balance))
                else:
                    new_amount_currency = 0.0

                if new_amount_currency != amount_currency:
                    line.sudo().with_context(**ctx).write({
                        "amount_currency": new_amount_currency,
                    })

    def _set_landed_cost_cogs_analytic_fast(self):
        StockMove = self.env["stock.move"]

        ctx = {
            "check_move_validity": False,
            "skip_account_move_synchronization": True,
            "skip_invoice_sync": True,
            "skip_invoice_line_sync": True,
            "skip_move_branch_default": True,
        }

        for move in self:
            if move.state != "draft":
                continue

            landed_cost = move._get_landed_cost_record()
            if not landed_cost:
                continue

            valuation_lines = landed_cost.valuation_adjustment_lines.filtered(
                lambda l: l.move_id and l.move_id.product_id
            )

            products = valuation_lines.mapped("move_id.product_id")
            if not products:
                continue

            outgoing_moves = StockMove.search([
                ("product_id", "in", products.ids),
                ("state", "=", "done"),
                ("picking_id.picking_type_id.code", "=", "outgoing"),
                ("sale_line_id", "!=", False),
                ("date", "<=", landed_cost.date),
            ], order="product_id, date desc")

            analytic_by_product = {}

            for out_move in outgoing_moves:
                product_id = out_move.product_id.id

                if product_id in analytic_by_product:
                    continue

                analytic = (
                    out_move.sale_line_id.order_id.analytic_account_id
                    or out_move.picking_id.sale_id.analytic_account_id
                    or out_move.picking_id.analytic_account_id
                )

                if analytic:
                    analytic_by_product[product_id] = analytic

            if not analytic_by_product:
                continue

            cogs_lines = move.line_ids.filtered(
                lambda line:
                not line.analytic_distribution
                and not line.is_branch_distribution_line
                and line.account_id.account_type in (
                    "expense",
                    "expense_direct_cost",
                    "expense_depreciation",
                )
            )

            for line in cogs_lines:
                analytic = False

                if line.product_id and line.product_id.id in analytic_by_product:
                    analytic = analytic_by_product[line.product_id.id]

                if not analytic:
                    line_name = (line.name or "").lower()

                    for product in products:
                        names = [
                            product.display_name or "",
                            product.name or "",
                            product.default_code or "",
                        ]

                        if any(name and str(name).lower() in line_name for name in names):
                            analytic = analytic_by_product.get(product.id)
                            if analytic:
                                break

                if not analytic:
                    continue

                vals = {
                    "analytic_distribution": {str(analytic.id): 100.0},
                }

                branch_line = analytic.branch_distribution_line_ids[:1]
                if branch_line and branch_line.branch_id:
                    vals["branch_id"] = branch_line.branch_id.id

                line.sudo().with_context(**ctx).write(vals)

    def _split_positive_amount_by_percentages(self, total_amount, branch_percentages, currency):
        rounding = currency.rounding or 0.01
        result = {branch_id: 0.0 for branch_id in branch_percentages}

        total_amount = total_amount or 0.0
        if float_is_zero(total_amount, precision_rounding=rounding):
            return result

        total_units = int(round(total_amount / rounding))
        items = []
        used_units = 0

        for branch_id, pct in branch_percentages.items():
            raw_units = (total_units * (pct or 0.0)) / 100.0
            floor_units = int(raw_units)
            remainder = raw_units - floor_units

            items.append({
                "branch_id": branch_id,
                "units": floor_units,
                "remainder": remainder,
            })
            used_units += floor_units

        remaining_units = total_units - used_units
        items.sort(key=lambda x: x["remainder"], reverse=True)

        for item in items:
            if remaining_units <= 0:
                break
            item["units"] += 1
            remaining_units -= 1

        for item in items:
            result[item["branch_id"]] = item["units"] * rounding

        return result

    def _prepare_branch_distribution_amounts(
        self,
        original_debit,
        original_credit,
        original_amount_currency,
        branch_percentages,
        company_currency,
        line_currency=False,
    ):
        original_debit = original_debit or 0.0
        original_credit = original_credit or 0.0
        original_amount_currency = original_amount_currency or 0.0

        if original_debit:
            debit_by_branch = self._split_positive_amount_by_percentages(
                original_debit,
                branch_percentages,
                company_currency,
            )
            credit_by_branch = {branch_id: 0.0 for branch_id in branch_percentages}
        elif original_credit:
            credit_by_branch = self._split_positive_amount_by_percentages(
                original_credit,
                branch_percentages,
                company_currency,
            )
            debit_by_branch = {branch_id: 0.0 for branch_id in branch_percentages}
        else:
            debit_by_branch = {branch_id: 0.0 for branch_id in branch_percentages}
            credit_by_branch = {branch_id: 0.0 for branch_id in branch_percentages}

        amount_currency_by_branch = {branch_id: 0.0 for branch_id in branch_percentages}

        if line_currency:
            if line_currency == company_currency:
                amount_currency_by_branch = {
                    branch_id: (
                        debit_by_branch.get(branch_id, 0.0)
                        - credit_by_branch.get(branch_id, 0.0)
                    )
                    for branch_id in branch_percentages
                }
            else:
                amount_currency_abs = abs(original_amount_currency)

                amount_currency_abs_by_branch = self._split_positive_amount_by_percentages(
                    amount_currency_abs,
                    branch_percentages,
                    line_currency,
                )

                amount_currency_by_branch = {}

                for branch_id in branch_percentages:
                    amount = amount_currency_abs_by_branch.get(branch_id, 0.0)

                    if debit_by_branch.get(branch_id, 0.0):
                        amount_currency_by_branch[branch_id] = abs(amount)
                    elif credit_by_branch.get(branch_id, 0.0):
                        amount_currency_by_branch[branch_id] = -abs(amount)
                    else:
                        amount_currency_by_branch[branch_id] = 0.0

        return debit_by_branch, credit_by_branch, amount_currency_by_branch

    def _get_branch_distribution_data_from_line(self, line_ctx):
        allocations = {}

        for analytic_id, percentage in self._get_safe_analytic_items_from_distribution(
            line_ctx.analytic_distribution
        ):
            if float_is_zero(percentage or 0.0, precision_rounding=1e-12):
                continue

            analytic = self.env["account.analytic.account"].browse(analytic_id).exists()
            if not analytic:
                continue

            for bl in analytic.branch_distribution_line_ids:
                if not bl.branch_id:
                    continue

                b_pct = ((percentage or 0.0) * (bl.percentage or 0.0)) / 100.0
                if float_is_zero(b_pct, precision_rounding=1e-12):
                    continue

                allocations.setdefault(bl.branch_id.id, {})
                allocations[bl.branch_id.id][analytic.id] = (
                    allocations[bl.branch_id.id].get(analytic.id, 0.0) + b_pct
                )

        total_pct = sum(sum(a_map.values()) for a_map in allocations.values())
        if not allocations or float_is_zero(total_pct, precision_rounding=1e-9):
            return {}, {}

        normalize_factor = 100.0 / total_pct
        branch_percentages = {}
        branch_distributions = {}

        for branch_id in sorted(allocations.keys()):
            a_map = allocations[branch_id]
            branch_total = sum(a_map.values())
            if float_is_zero(branch_total, precision_rounding=1e-12):
                continue

            branch_percentages[branch_id] = branch_total * normalize_factor
            branch_distributions[branch_id] = {
                str(a_id): (pct / branch_total) * 100.0
                for a_id, pct in a_map.items()
            }

        return branch_percentages, branch_distributions

    def _cleanup_branch_distribution_lines(self, pnl_account_types):
        self.ensure_one()

        ctx = {
            "check_move_validity": False,
            "skip_account_move_synchronization": True,
            "skip_invoice_sync": True,
            "skip_invoice_line_sync": True,
            "skip_move_branch_default": True,
        }

        self.with_context(**ctx)._reverse_branch_distribution_lines()
        self.invalidate_recordset(["line_ids"])

        split_lines = self.line_ids.filtered(
            lambda l:
            l.account_id.account_type in pnl_account_types
            and l.analytic_distribution
            and l.is_branch_distribution_line
        )

        if not split_lines:
            return

        grouped = {}

        for line in split_lines:
            group_key = (
                line.account_id.id,
                line.name or "",
                line.partner_id.id or False,
                line.analytic_tag_id.id or False,
                line.display_type or "product",
            )
            grouped.setdefault(group_key, self.env["account.move.line"])
            grouped[group_key] |= line

        for group_lines in grouped.values():
            main_line = group_lines.filtered(
                lambda l: l.display_type in (False, "product")
            )[:1] or group_lines[:1]

            other_lines = group_lines - main_line

            total_balance = sum(
                (l.debit or 0.0) - (l.credit or 0.0)
                for l in group_lines
            )

            if total_balance >= 0:
                total_debit = total_balance
                total_credit = 0.0
            else:
                total_debit = 0.0
                total_credit = abs(total_balance)

            total_amount_currency = sum(group_lines.mapped("amount_currency"))

            merged_distribution = {}
            total_weight = 0.0

            for old_line in group_lines:
                weight = (
                    abs((old_line.debit or 0.0) - (old_line.credit or 0.0))
                    or abs(old_line.amount_currency or 0.0)
                    or 0.0
                )
                if not weight:
                    continue

                total_weight += weight

                for analytic_id, pct in (old_line.analytic_distribution or {}).items():
                    for part in str(analytic_id).split(','):
                        part = part.strip()
                        if not part.isdigit():
                            continue

                        merged_distribution[part] = (
                            merged_distribution.get(part, 0.0) + (pct * weight)
                        )

            if total_weight:
                merged_distribution = {
                    analytic_id: value / total_weight
                    for analytic_id, value in merged_distribution.items()
                }

            analytic_tag = group_lines.mapped("analytic_tag_id")[:1]

            fixed_amount_currency = self._fix_amount_currency_sign(
                main_line,
                total_debit,
                total_credit,
                total_amount_currency,
            )

            main_line.sudo().with_context(**ctx).write({
                "branch_id": self.branch_id.id if self.branch_id else False,
                "debit": total_debit,
                "credit": total_credit,
                "amount_currency": fixed_amount_currency,
                "analytic_distribution": merged_distribution,
                "is_branch_distribution_line": False,
                "analytic_tag_id": analytic_tag.id if analytic_tag else False,
                "branch_distribution_key": False,
                "branch_distribution_note": _("Cleaned old branch distribution by net balance"),
                "display_type": "product",
            })

            if other_lines:
                other_lines.sudo().with_context(**ctx).unlink()

        self.invalidate_recordset(["line_ids"])

    # Landed cost fast path
    # Landed cost fast path
    def _post(self, soft=True):
        self = self.with_context(skip_posted_analytic_branch_check=True)

        pnl_account_types = (
            'income',
            'income_other',
            'expense',
            'expense_depreciation',
            'expense_direct_cost',
        )

        landed_cost_moves = self.filtered(
            lambda m: m.state == "draft" and m._is_landed_cost_move()
        )
        normal_moves = self - landed_cost_moves

        if landed_cost_moves:
            landed_cost_moves._set_landed_cost_cogs_analytic_fast()
            landed_cost_moves._sanitize_landed_cost_amount_currency()

        deferred_bill_moves = self.env["account.move"]

        for move in normal_moves:
            move._set_negative_inventory_revaluation_analytic(move)

            if move.state != 'draft':
                continue

            move._cleanup_branch_distribution_lines(pnl_account_types)
            move.invalidate_recordset(["line_ids"])

            if move.move_type in ('in_invoice', 'in_refund'):
                first_bill_line = move.invoice_line_ids.filtered(
                    lambda l: l.analytic_distribution
                )[:1]

                default_analytic_distribution = (
                    first_bill_line.analytic_distribution
                    if first_bill_line else False
                )

                if default_analytic_distribution:
                    exchange_loss_lines = move.line_ids.filtered(
                        lambda l:
                        not l.analytic_distribution
                        and not l.is_branch_distribution_line
                        and (
                            l.account_id.code == '400053'
                            or 'loss on difference on exchange' in (l.name or '').lower()
                            or 'gain on difference on exchange' in (l.name or '').lower()
                            or 'exchange' in (l.account_id.display_name or '').lower()
                        )
                    )

                    if exchange_loss_lines:
                        exchange_vals = {
                            'analytic_distribution': default_analytic_distribution,
                        }

                        if first_bill_line.branch_id:
                            exchange_vals['branch_id'] = first_bill_line.branch_id.id

                        exchange_loss_lines.with_context(
                            check_move_validity=False,
                            skip_account_move_synchronization=True,
                            skip_invoice_sync=True,
                            skip_invoice_line_sync=True,
                            skip_move_branch_default=True,
                        ).write(exchange_vals)

            no_analytic_lines = move.line_ids.filtered(
                lambda l:
                l.account_id.account_type in pnl_account_types
                and not l.analytic_distribution
                and not l.is_branch_distribution_line
            )

            if no_analytic_lines:
                accounts = '\n'.join(
                    f"- {account}"
                    for account in no_analytic_lines.mapped('account_id.display_name')
                )
                raise ValidationError(
                    _("You can't post entry without analytic distribution for the account(s):\n%s") % accounts
                )

            if move.is_invoice(include_receipts=True):

                if move.move_type in ('out_invoice', 'out_refund'):
                    if move.branch_id:
                        move.line_ids.with_context(
                            check_move_validity=False,
                            skip_account_move_synchronization=True,
                            skip_invoice_sync=True,
                            skip_invoice_line_sync=True,
                            skip_move_branch_default=True,
                        ).write({
                            'branch_id': move.branch_id.id,
                        })

                    invoice_lines = move.line_ids.filtered(
                        lambda l:
                        l.account_id.account_type in pnl_account_types
                        and l.analytic_distribution
                        and not l.is_branch_distribution_line
                    )

                    invoice_branch_errors = []

                    for line in invoice_lines:
                        for analytic_id, percentage in self._get_safe_analytic_items_from_distribution(
                            line.analytic_distribution
                        ):
                            if not percentage:
                                continue

                            analytic = self.env['account.analytic.account'].browse(analytic_id).exists()
                            if not analytic:
                                continue

                            analytic_branches = analytic.branch_distribution_line_ids.mapped('branch_id')

                            if not analytic_branches:
                                invoice_branch_errors.append(analytic.display_name)
                                continue

                            if len(analytic_branches) == 1 and move.branch_id != analytic_branches[0]:
                                invoice_branch_errors.append(analytic.display_name)

                    if invoice_branch_errors:
                        raise ValidationError(
                            _("Invoice branch must be the same as the analytic branch distribution.")
                        )

                if move.move_type in ('in_invoice', 'in_refund'):
                    if move.branch_id:
                        normal_lines = move.line_ids.filtered(
                            lambda l: not l.is_branch_distribution_line
                        )
                        normal_lines.with_context(
                            check_move_validity=False,
                            skip_account_move_synchronization=True,
                            skip_invoice_sync=True,
                            skip_invoice_line_sync=True,
                            skip_move_branch_default=True,
                        ).write({
                            'branch_id': move.branch_id.id,
                        })

                    invoice_lines = move.line_ids.filtered(
                        lambda l:
                        l.account_id.account_type in pnl_account_types
                        and l.analytic_distribution
                        and not l.is_branch_distribution_line
                    )

                    bill_analytic_branches = self.env['res.branch']

                    for line in invoice_lines:
                        for analytic_id, percentage in self._get_safe_analytic_items_from_distribution(
                            line.analytic_distribution
                        ):
                            if not percentage:
                                continue

                            analytic = self.env['account.analytic.account'].browse(analytic_id).exists()
                            if not analytic:
                                continue

                            analytic_branches = analytic.branch_distribution_line_ids.mapped('branch_id')

                            if len(analytic_branches) == 1:
                                bill_analytic_branches |= analytic_branches[0]
                            elif len(analytic_branches) > 1:
                                bill_analytic_branches |= analytic_branches

                    if (
                        move.branch_id
                        and len(bill_analytic_branches) == 1
                        and move.branch_id != bill_analytic_branches[0]
                    ):
                        raise ValidationError(
                            _("Bill branch must be the same as the analytic branch distribution.")
                        )

                    deferred_lines = invoice_lines.filtered(
                        lambda l:
                        getattr(l, "deferred_start_date", False)
                        or getattr(l, "deferred_end_date", False)
                    )

                    normal_invoice_lines = invoice_lines - deferred_lines

                    for line in normal_invoice_lines:
                        move._apply_bill_branch_distribution_no_duplicate(line)

                    if deferred_lines:
                        deferred_bill_moves |= move

                continue

            no_branch_errors = []

            for line in move.line_ids.filtered(lambda l: not l.is_branch_distribution_line):
                if line.account_id.account_type not in pnl_account_types:
                    continue

                for analytic_id, percentage in self._get_safe_analytic_items_from_distribution(
                    line.analytic_distribution
                ):
                    if not percentage:
                        continue

                    analytic = self.env['account.analytic.account'].browse(analytic_id).exists()
                    if analytic and not analytic.branch_distribution_line_ids:
                        no_branch_errors.append(
                            _("- %(analytic)s") % {'analytic': analytic.display_name}
                        )

            if no_branch_errors:
                raise ValidationError(
                    _("You can't post entry because branch is missing on the analytic account(s):\n%s")
                    % '\n'.join(no_branch_errors)
                )

            lines_to_distribute = move.line_ids.filtered(
                lambda l:
                l.exists()
                and l.account_id.account_type in pnl_account_types
                and l.analytic_distribution
                and not l.is_branch_distribution_line
            )

            for line in lines_to_distribute:
                move.apply_branch_distribution(line)

        posted_moves = super(AccountMoveInherit, self)._post(soft=soft)

        for move in deferred_bill_moves:
            move._distribute_deferred_bill_journal_items_after_post(pnl_account_types)

        return posted_moves

    def onchange_branch_id(self):
        for move in self:
            if move.branch_id and move.is_invoice(include_receipts=True):
                for line in move.line_ids:
                    line.branch_id = move.branch_id

    def apply_branch_distribution(self, line):
        self.ensure_one()

        if (
            not bool(self.statement_line_id)
            and self.state != "draft"
        ) or not line.exists() or not line.analytic_distribution:
            return line

        ctx = {
            "check_move_validity": False,
            "skip_account_move_synchronization": True,
            "skip_invoice_sync": True,
            "skip_invoice_line_sync": True,
            "skip_move_branch_default": True,
        }

        line_ctx = line.sudo().with_context(**ctx)

        if line_ctx.is_branch_distribution_line:
            return line_ctx

        if (
            line_ctx.account_id == self.journal_id.default_account_id
            or line_ctx.account_id.account_type in ("asset_cash", "liability_credit_card")
        ):
            line_ctx.with_context(**ctx).write({
                "branch_distribution_note": _("Skipped: bank/cash line cannot be split.")
            })
            return line_ctx

        company_currency = line_ctx.company_id.currency_id
        line_currency = line_ctx.currency_id
        keep_currency = bool(line_currency)

        MoveLine = self.env["account.move.line"].sudo().with_context(**ctx)

        branch_percentages, branch_distributions = self._get_branch_distribution_data_from_line(line_ctx)

        if not branch_percentages:
            line_ctx.with_context(**ctx).write({
                "branch_distribution_note": _("No Branch Distribution on Analytic")
            })
            return line_ctx

        dist_key = line_ctx.branch_distribution_key or str(uuid.uuid4())
        old_branch_name = line_ctx.branch_id.display_name if line_ctx.branch_id else _("No Branch")

        if len(branch_percentages) == 1:
            branch_id = next(iter(branch_percentages))
            branch = self.env["res.branch"].browse(branch_id).exists()

            fixed_amount_currency = self._fix_amount_currency_sign(
                line_ctx,
                line_ctx.debit,
                line_ctx.credit,
                line_ctx.amount_currency,
            )

            line_ctx.with_context(**ctx).write({
                "branch_id": branch_id,
                "analytic_distribution": branch_distributions[branch_id],
                "amount_currency": fixed_amount_currency,
                "is_branch_distribution_line": True,
                "analytic_tag_id": line_ctx.analytic_tag_id.id or False,
                "branch_distribution_key": dist_key,
                "branch_distribution_note": _("Updated: %(old)s → %(new)s") % {
                    "old": old_branch_name,
                    "new": branch.display_name if branch else branch_id,
                },
            })
            return line_ctx

        debit_by_branch, credit_by_branch, amount_currency_by_branch = self._prepare_branch_distribution_amounts(
            line_ctx.debit,
            line_ctx.credit,
            line_ctx.amount_currency,
            branch_percentages,
            company_currency,
            line_currency if keep_currency else False,
        )

        new_lines_vals = []

        for branch_id in sorted(branch_percentages.keys()):
            branch = self.env["res.branch"].browse(branch_id).exists()

            debit = debit_by_branch.get(branch_id, 0.0)
            credit = credit_by_branch.get(branch_id, 0.0)
            amount_currency = amount_currency_by_branch.get(branch_id, 0.0)

            vals = {
                "move_id": line_ctx.move_id.id,
                "account_id": line_ctx.account_id.id,
                "partner_id": line_ctx.partner_id.id or False,
                "name": line_ctx.name,
                "date_maturity": line_ctx.date_maturity,
                "branch_id": branch_id,
                "analytic_distribution": branch_distributions[branch_id],
                "is_branch_distribution_line": True,
                "analytic_tag_id": line_ctx.analytic_tag_id.id or False,
                "branch_distribution_key": dist_key,
                "branch_distribution_note": _("Split: %(old)s → %(new)s") % {
                    "old": old_branch_name,
                    "new": branch.display_name if branch else branch_id,
                },
                "company_id": line_ctx.company_id.id,
                "display_type": line_ctx.display_type or "product",
                "debit": debit,
                "credit": credit,
                "amount_currency": amount_currency,
            }

            if line_currency:
                vals["currency_id"] = line_currency.id

            new_lines_vals.append(vals)

        if len(new_lines_vals) <= 1:
            return line_ctx

        created_lines = MoveLine.create(new_lines_vals)
        line_ctx.with_context(**ctx).unlink()

        return created_lines

    def _distribute_deferred_bill_journal_items_after_post(self, pnl_account_types):
        ctx = {
            "check_move_validity": False,
            "skip_account_move_synchronization": True,
            "skip_invoice_sync": True,
            "skip_invoice_line_sync": True,
            "skip_move_branch_default": True,
        }

        for move in self:
            if move.move_type not in ("in_invoice", "in_refund"):
                continue

            deferred_lines = move.invoice_line_ids.filtered(
                lambda l:
                l.account_id.account_type in pnl_account_types
                and l.analytic_distribution
                and not l.is_branch_distribution_line
                and (
                    getattr(l, "deferred_start_date", False)
                    or getattr(l, "deferred_end_date", False)
                )
            )

            for line in deferred_lines:
                branch_percentages, branch_distributions = move._get_branch_distribution_data_from_line(line)

                if not branch_percentages:
                    continue

                if len(branch_percentages) == 1:
                    branch_id = next(iter(branch_percentages))
                    line.sudo().with_context(**ctx).write({
                        "branch_id": branch_id,
                        "branch_distribution_note": _("Deferred bill line branch updated after posting."),
                    })
                    continue

                move._apply_posted_deferred_bill_line_distribution(line)

            move._distribute_related_deferred_entries(pnl_account_types)

    def _apply_posted_deferred_bill_line_distribution(self, line):
        self.ensure_one()

        ctx = {
            "check_move_validity": False,
            "skip_account_move_synchronization": True,
            "skip_invoice_sync": True,
            "skip_invoice_line_sync": True,
            "skip_move_branch_default": True,
        }

        line_ctx = line.sudo().with_context(**ctx)

        if line_ctx.is_branch_distribution_line:
            return line_ctx

        company_currency = line_ctx.company_id.currency_id
        line_currency = line_ctx.currency_id or company_currency

        branch_percentages, branch_distributions = self._get_branch_distribution_data_from_line(line_ctx)

        if not branch_percentages:
            return line_ctx

        dist_key = str(uuid.uuid4())
        old_branch_name = line_ctx.branch_id.display_name if line_ctx.branch_id else _("No Branch")

        debit_by_branch, credit_by_branch, amount_currency_by_branch = self._prepare_branch_distribution_amounts(
            line_ctx.debit,
            line_ctx.credit,
            line_ctx.amount_currency,
            branch_percentages,
            company_currency,
            line_currency,
        )

        split_vals_list = []

        for branch_id in sorted(branch_percentages.keys()):
            debit = debit_by_branch.get(branch_id, 0.0)
            credit = credit_by_branch.get(branch_id, 0.0)

            if company_currency.is_zero(debit) and company_currency.is_zero(credit):
                continue

            amount_currency = amount_currency_by_branch.get(branch_id, 0.0)

            if line_currency == company_currency:
                amount_currency = debit - credit
            elif debit > 0:
                amount_currency = abs(amount_currency) or abs(debit - credit)
            elif credit > 0:
                amount_currency = -(abs(amount_currency) or abs(debit - credit))
            else:
                continue

            branch = self.env["res.branch"].browse(branch_id).exists()

            split_vals_list.append({
                "branch_id": branch_id,
                "analytic_distribution": branch_distributions[branch_id],
                "debit": debit,
                "credit": credit,
                "currency_id": line_currency.id,
                "amount_currency": amount_currency,
                "is_branch_distribution_line": True,
                "analytic_tag_id": line_ctx.analytic_tag_id.id or False,
                "branch_distribution_key": dist_key,
                "branch_distribution_note": _("Deferred bill journal distribution: %(old)s → %(new)s") % {
                    "old": old_branch_name,
                    "new": branch.display_name if branch else branch_id,
                },
            })

        if not split_vals_list:
            return line_ctx

        MoveLine = self.env["account.move.line"].sudo().with_context(**ctx)

        first_done = False

        for split_vals in split_vals_list:
            if not first_done:
                line_ctx.with_context(**ctx).write({
                    "branch_id": split_vals["branch_id"],
                    "analytic_distribution": split_vals["analytic_distribution"],
                    "debit": split_vals["debit"],
                    "credit": split_vals["credit"],
                    "currency_id": split_vals["currency_id"],
                    "amount_currency": split_vals["amount_currency"],
                    "is_branch_distribution_line": True,
                    "analytic_tag_id": split_vals["analytic_tag_id"],
                    "branch_distribution_key": split_vals["branch_distribution_key"],
                    "branch_distribution_note": split_vals["branch_distribution_note"],
                    "display_type": line_ctx.display_type or "product",
                })
                first_done = True
            else:
                MoveLine.create({
                    "move_id": self.id,
                    "account_id": line_ctx.account_id.id,
                    "partner_id": line_ctx.partner_id.id or False,
                    "name": line_ctx.name,
                    "date_maturity": line_ctx.date_maturity,
                    "company_id": line_ctx.company_id.id,
                    "currency_id": split_vals["currency_id"],
                    "debit": split_vals["debit"],
                    "credit": split_vals["credit"],
                    "amount_currency": split_vals["amount_currency"],
                    "branch_id": split_vals["branch_id"],
                    "analytic_distribution": split_vals["analytic_distribution"],
                    "is_branch_distribution_line": True,
                    "analytic_tag_id": split_vals["analytic_tag_id"],
                    "branch_distribution_key": split_vals["branch_distribution_key"],
                    "branch_distribution_note": split_vals["branch_distribution_note"],
                    "display_type": "cogs",
                    "tax_ids": [(6, 0, [])],
                })

        return line_ctx

    def _distribute_related_deferred_entries(self, pnl_account_types):
        Move = self.env["account.move"]
        MoveLine = self.env["account.move.line"]
        candidate_moves = Move

        for move in self:
            domain_parts = []

            if "deferred_origin_move_id" in Move._fields:
                domain_parts.append([("deferred_origin_move_id", "=", move.id)])

            if "deferred_original_move_id" in Move._fields:
                domain_parts.append([("deferred_original_move_id", "=", move.id)])

            if "original_move_id" in Move._fields:
                domain_parts.append([("original_move_id", "=", move.id)])

            if "deferred_origin_move_line_id" in MoveLine._fields:
                origin_lines = move.invoice_line_ids.filtered(
                    lambda l:
                    getattr(l, "deferred_start_date", False)
                    or getattr(l, "deferred_end_date", False)
                )
                if origin_lines:
                    linked_lines = MoveLine.search([
                        ("deferred_origin_move_line_id", "in", origin_lines.ids),
                        ("move_id", "!=", move.id),
                    ])
                    candidate_moves |= linked_lines.mapped("move_id")

            for domain in domain_parts:
                candidate_moves |= Move.search(domain)

        candidate_moves = candidate_moves.filtered(
            lambda m:
            m.state == "draft"
            and not m.is_invoice(include_receipts=True)
        )

        for deferred_move in candidate_moves:
            lines_to_distribute = deferred_move.line_ids.filtered(
                lambda l:
                l.exists()
                and l.account_id.account_type in pnl_account_types
                and l.analytic_distribution
                and not l.is_branch_distribution_line
            )

            for line in lines_to_distribute:
                deferred_move.apply_branch_distribution(line)

    def _apply_bill_branch_distribution_no_duplicate(self, line):
        self.ensure_one()

        if not line.exists() or not line.analytic_distribution:
            return line

        ctx = {
            "check_move_validity": False,
            "skip_account_move_synchronization": True,
            "skip_invoice_sync": True,
            "skip_invoice_line_sync": True,
            "skip_move_branch_default": True,
        }

        line_ctx = line.sudo().with_context(**ctx)

        if line_ctx.is_branch_distribution_line:
            return line_ctx

        has_deferred_dates = (
            getattr(line_ctx, "deferred_start_date", False)
            or getattr(line_ctx, "deferred_end_date", False)
        )

        company_currency = line_ctx.company_id.currency_id
        line_currency = line_ctx.currency_id or company_currency

        branch_percentages, branch_distributions = self._get_branch_distribution_data_from_line(line_ctx)

        if not branch_percentages:
            line_ctx.with_context(**ctx).write({
                "branch_distribution_note": _("No Branch Distribution on Analytic")
            })
            return line_ctx

        if has_deferred_dates and len(branch_percentages) == 1:
            branch_id = next(iter(branch_percentages))

            fixed_amount_currency = self._fix_amount_currency_sign(
                line_ctx,
                line_ctx.debit,
                line_ctx.credit,
                line_ctx.amount_currency,
            )

            line_ctx.with_context(**ctx).write({
                "branch_id": branch_id,
                "amount_currency": fixed_amount_currency,
                "branch_distribution_note": _("Updated deferred bill line branch from analytic branch distribution."),
            })
            return line_ctx

        if has_deferred_dates and len(branch_percentages) > 1:
            line_ctx.with_context(**ctx).write({
                "branch_distribution_note": _("Deferred shared analytic kept before posting. Distribution is applied after posting."),
            })
            return line_ctx

        dist_key = str(uuid.uuid4())
        old_branch_name = line_ctx.branch_id.display_name if line_ctx.branch_id else _("No Branch")

        debit_by_branch, credit_by_branch, amount_currency_by_branch = self._prepare_branch_distribution_amounts(
            line_ctx.debit,
            line_ctx.credit,
            line_ctx.amount_currency,
            branch_percentages,
            company_currency,
            line_currency,
        )

        split_vals_list = []

        for branch_id in sorted(branch_percentages.keys()):
            debit = debit_by_branch.get(branch_id, 0.0)
            credit = credit_by_branch.get(branch_id, 0.0)

            if company_currency.is_zero(debit) and company_currency.is_zero(credit):
                continue

            amount_currency = amount_currency_by_branch.get(branch_id, 0.0)

            if line_currency == company_currency:
                amount_currency = debit - credit
            elif debit > 0:
                amount_currency = abs(amount_currency) or abs(debit - credit)
            elif credit > 0:
                amount_currency = -(abs(amount_currency) or abs(debit - credit))
            else:
                continue

            branch = self.env["res.branch"].browse(branch_id).exists()

            split_vals_list.append({
                "branch_id": branch_id,
                "analytic_distribution": branch_distributions[branch_id],
                "debit": debit,
                "credit": credit,
                "currency_id": line_currency.id,
                "amount_currency": amount_currency,
                "is_branch_distribution_line": True,
                "analytic_tag_id": line_ctx.analytic_tag_id.id or False,
                "branch_distribution_key": dist_key,
                "branch_distribution_note": _("Bill branch distribution: %(old)s → %(new)s") % {
                    "old": old_branch_name,
                    "new": branch.display_name if branch else branch_id,
                },
            })

        if not split_vals_list:
            line_ctx.with_context(**ctx).write({
                "branch_distribution_note": _("Skipped: branch distribution generated zero amount lines only."),
            })
            return line_ctx

        MoveLine = self.env["account.move.line"].sudo().with_context(**ctx)

        first_done = False

        for split_vals in split_vals_list:
            if not first_done:
                line_ctx.with_context(**ctx).write({
                    "branch_id": split_vals["branch_id"],
                    "analytic_distribution": split_vals["analytic_distribution"],
                    "debit": split_vals["debit"],
                    "credit": split_vals["credit"],
                    "currency_id": split_vals["currency_id"],
                    "amount_currency": split_vals["amount_currency"],
                    "is_branch_distribution_line": True,
                    "analytic_tag_id": split_vals["analytic_tag_id"],
                    "branch_distribution_key": split_vals["branch_distribution_key"],
                    "branch_distribution_note": split_vals["branch_distribution_note"],
                    "display_type": line_ctx.display_type or "product",
                })
                first_done = True
            else:
                MoveLine.create({
                    "move_id": self.id,
                    "account_id": line_ctx.account_id.id,
                    "partner_id": line_ctx.partner_id.id or False,
                    "name": line_ctx.name,
                    "date_maturity": line_ctx.date_maturity,
                    "company_id": line_ctx.company_id.id,
                    "currency_id": split_vals["currency_id"],
                    "debit": split_vals["debit"],
                    "credit": split_vals["credit"],
                    "amount_currency": split_vals["amount_currency"],
                    "branch_id": split_vals["branch_id"],
                    "analytic_distribution": split_vals["analytic_distribution"],
                    "is_branch_distribution_line": True,
                    "analytic_tag_id": split_vals["analytic_tag_id"],
                    "branch_distribution_key": split_vals["branch_distribution_key"],
                    "branch_distribution_note": split_vals["branch_distribution_note"],
                    "display_type": "cogs",
                    "tax_ids": [(6, 0, [])],
                })

        return line_ctx

    def button_draft(self):
        ctx = {
            "check_move_validity": False,
            "skip_account_move_synchronization": True,
            "skip_invoice_sync": True,
            "skip_invoice_line_sync": True,
            "skip_move_branch_default": True,
        }

        moves = self.with_context(**ctx)

        for move in moves:
            split_lines = move.line_ids.filtered(
                lambda l:
                l.is_branch_distribution_line
                and l.branch_distribution_key
                and l.display_type == "cogs"
            )

            if split_lines:
                split_lines.sudo().with_context(**ctx).write({
                    "display_type": "product",
                })

        res = super(AccountMoveInherit, moves).button_draft()

        pnl_account_types = (
            'income',
            'income_other',
            'expense',
            'expense_depreciation',
            'expense_direct_cost',
        )

        for move in moves:
            move.with_context(**ctx)._cleanup_branch_distribution_lines(pnl_account_types)

        return res

    def _reverse_branch_distribution_lines(self):
        self.ensure_one()

        ctx = {
            "check_move_validity": False,
            "skip_account_move_synchronization": True,
            "skip_invoice_sync": True,
            "skip_invoice_line_sync": True,
            "skip_move_branch_default": True,
        }

        dist_lines = self.line_ids.filtered(
            lambda l:
            l.is_branch_distribution_line
            and l.branch_distribution_key
        )

        keys = list(set(dist_lines.mapped("branch_distribution_key")))

        for key in keys:
            lines = self.line_ids.filtered(
                lambda l:
                l.is_branch_distribution_line
                and l.branch_distribution_key == key
            )

            if not lines:
                continue

            main_line = lines.filtered(
                lambda l: l.display_type in (False, "product")
            )[:1] or lines[:1]

            other_lines = lines - main_line

            total_balance = sum(
                (l.debit or 0.0) - (l.credit or 0.0)
                for l in lines
            )

            if total_balance >= 0:
                total_debit = total_balance
                total_credit = 0.0
            else:
                total_debit = 0.0
                total_credit = abs(total_balance)

            total_amount_currency = sum(lines.mapped("amount_currency"))

            merged_distribution = {}
            total_weight = 0.0

            for old_line in lines:
                weight = (
                    abs((old_line.debit or 0.0) - (old_line.credit or 0.0))
                    or abs(old_line.amount_currency or 0.0)
                    or 0.0
                )

                if not weight:
                    continue

                total_weight += weight

                for analytic_id, pct in (old_line.analytic_distribution or {}).items():
                    for part in str(analytic_id).split(','):
                        part = part.strip()
                        if not part.isdigit():
                            continue

                        merged_distribution[part] = (
                            merged_distribution.get(part, 0.0) + (pct * weight)
                        )

            if total_weight:
                merged_distribution = {
                    analytic_id: value / total_weight
                    for analytic_id, value in merged_distribution.items()
                }

            analytic_tag = lines.mapped("analytic_tag_id")[:1]

            fixed_amount_currency = self._fix_amount_currency_sign(
                main_line,
                total_debit,
                total_credit,
                total_amount_currency,
            )

            main_line.sudo().with_context(**ctx).write({
                "branch_id": self.branch_id.id if self.branch_id else False,
                "debit": total_debit,
                "credit": total_credit,
                "amount_currency": fixed_amount_currency,
                "analytic_distribution": merged_distribution,
                "is_branch_distribution_line": False,
                "analytic_tag_id": analytic_tag.id if analytic_tag else False,
                "branch_distribution_key": False,
                "branch_distribution_note": _("Reversed branch distribution by net balance"),
                "display_type": "product",
            })

            if other_lines:
                other_lines.sudo().with_context(**ctx).unlink()

    def _set_negative_inventory_revaluation_analytic(self, moves):
        for move in moves:
            ref_text = " ".join(filter(None, [
                move.ref,
                move.name,
                move.narration,
            ]))

            if not ref_text:
                continue

            if "negative inventory" not in ref_text.lower():
                continue

            match = re.search(r"([A-Z0-9]+/\d{4}/OUT/\d+)", ref_text)
            if not match:
                continue

            picking_name = match.group(1)

            picking = self.env["stock.picking"].search([
                ("name", "ilike", picking_name)
            ], limit=1)

            if not picking or not picking.sale_id:
                continue

            sale = picking.sale_id
            analytic = sale.analytic_account_id

            if not analytic:
                continue

            branch_line = analytic.branch_distribution_line_ids[:1]
            branch = branch_line.branch_id if branch_line else False
            analytic_distribution = {str(analytic.id): 100.0}

            if not move.line_ids:
                continue

            if branch:
                move.with_context(check_move_validity=False).write({
                    "branch_id": branch.id,
                })

            vals = {"analytic_distribution": analytic_distribution}
            if branch:
                vals["branch_id"] = branch.id

            move.line_ids.with_context(
                check_move_validity=False,
                skip_account_move_synchronization=True,
            ).write(vals)

            move.message_post(body=_(
                "Analytic distribution and branch were updated automatically from Sale Order %s linked to Picking %s for negative inventory revaluation."
            ) % (sale.name, picking.name))

class StockLandedCostInherit(models.Model):
    _inherit = 'stock.landed.cost'

    def button_validate(self):
        res = super(
            StockLandedCostInherit,
            self.with_context(fix_landed_cost_amount_currency=True)
        ).button_validate()

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