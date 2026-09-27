# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    is_branch_distribution_line = fields.Boolean(
        copy=False,
        default=False,
    )
    branch_distribution_key = fields.Char(
        copy=False,
    )
    branch_distribution_note = fields.Char(
        copy=False,
    )
    analytic_tag_id = fields.Many2one(
        'analytic.tag',
    )
    budget_group_id = fields.Many2one(
        'budget.group',
        related='account_id.budget_group_id',
    )
    product_tag_id = fields.Many2one(
        'product.tag',
    )

    def _fix_landed_cost_amount_currency_vals(self, vals):
        vals = dict(vals or {})

        display_type = vals.get('display_type')

        if display_type not in (
            False,
            'product',
            'cogs',
        ):
            return vals

        move = False
        move_id = vals.get('move_id')

        if move_id:
            move = self.env['account.move'].browse(
                move_id
            ).exists()

        if vals.get('company_id'):
            company = self.env['res.company'].browse(
                vals['company_id']
            ).exists()
        elif move:
            company = move.company_id
        else:
            company = self.env.company

        if not company:
            return vals

        company_currency = company.currency_id
        currency = company_currency

        if vals.get('currency_id'):
            currency = (
                self.env['res.currency'].browse(
                    vals['currency_id']
                ).exists()
                or company_currency
            )

        debit = vals.get(
            'debit',
            0.0
        ) or 0.0

        credit = vals.get(
            'credit',
            0.0
        ) or 0.0

        if 'balance' in vals:
            balance = vals.get(
                'balance'
            ) or 0.0

            if balance > 0:
                debit = balance
                credit = 0.0
            elif balance < 0:
                debit = 0.0
                credit = abs(balance)
            else:
                debit = 0.0
                credit = 0.0

            vals['debit'] = debit
            vals['credit'] = credit
        else:
            balance = debit - credit

        if debit and credit:
            if balance >= 0:
                debit = abs(balance)
                credit = 0.0
            else:
                debit = 0.0
                credit = abs(balance)

            vals['debit'] = debit
            vals['credit'] = credit
            balance = debit - credit

        amount_currency = vals.get(
            'amount_currency',
            0.0
        ) or 0.0

        if currency == company_currency:
            vals['currency_id'] = (
                company_currency.id
            )
            vals['amount_currency'] = (
                balance
            )
        elif debit > 0:
            vals['amount_currency'] = (
                abs(amount_currency)
                or abs(balance)
            )
        elif credit > 0:
            vals['amount_currency'] = -(
                abs(amount_currency)
                or abs(balance)
            )
        else:
            vals['amount_currency'] = 0.0

        return vals

    @api.model
    def _get_analytic_ids_from_distribution(
        self,
        analytic_distribution
    ):
        analytic_ids = set()

        for key, percentage in (
            analytic_distribution or {}
        ).items():
            if not percentage:
                continue

            for analytic_id in str(key).split(','):
                analytic_id = analytic_id.strip()

                if analytic_id.isdigit():
                    analytic_ids.add(
                        int(analytic_id)
                    )

        return list(analytic_ids)

    @api.model
    def _get_analytics_from_distribution(
        self,
        analytic_distribution
    ):
        analytic_ids = (
            self._get_analytic_ids_from_distribution(
                analytic_distribution
            )
        )

        if not analytic_ids:
            return self.env[
                'account.analytic.account'
            ]

        return self.env[
            'account.analytic.account'
        ].browse(
            analytic_ids
        ).exists()

    @api.model
    def _get_analytic_branch_data(
        self,
        analytic_distribution
    ):
        analytics = (
            self._get_analytics_from_distribution(
                analytic_distribution
            )
        )

        all_branches = self.env[
            'res.branch'
        ]

        shared_analytics = self.env[
            'account.analytic.account'
        ]

        analytics_without_branch = self.env[
            'account.analytic.account'
        ]

        analytic_branch_map = {}

        for analytic in analytics:
            branches = (
                analytic
                .branch_distribution_line_ids
                .mapped('branch_id')
            )

            analytic_branch_map[
                analytic.id
            ] = branches

            all_branches |= branches

            if len(branches) > 1:
                shared_analytics |= analytic
            elif not branches:
                analytics_without_branch |= analytic

        return {
            'analytics': analytics,
            'branches': all_branches,
            'shared_analytics': shared_analytics,
            'analytics_without_branch': (
                analytics_without_branch
            ),
            'analytic_branch_map': (
                analytic_branch_map
            ),
        }

    @api.model
    def _analytic_distribution_changed(
        self,
        current_distribution,
        new_distribution
    ):
        return (
            (current_distribution or {})
            != (new_distribution or {})
        )

    def _prepare_posted_analytic_branch_vals(
        self,
        line,
        vals
    ):
        prepared_vals = dict(vals or {})

        if line.move_id.state != 'posted':
            return prepared_vals

        if 'analytic_distribution' not in prepared_vals:
            return prepared_vals

        new_distribution = (
            prepared_vals.get(
                'analytic_distribution'
            )
            or {}
        )

        new_data = (
            self._get_analytic_branch_data(
                new_distribution
            )
        )

        if not new_data['analytics']:
            return prepared_vals

        if new_data['shared_analytics']:
            return prepared_vals

        if new_data['analytics_without_branch']:
            return prepared_vals

        analytic_branches = (
            new_data['branches']
        )

        if len(analytic_branches) == 1:
            prepared_vals['branch_id'] = (
                analytic_branches.id
            )

        return prepared_vals

    def _check_posted_analytic_branch_update(
        self,
        vals
    ):
        analytic_in_vals = (
            'analytic_distribution' in vals
        )

        branch_in_vals = (
            'branch_id' in vals
        )

        if (
            not analytic_in_vals
            and not branch_in_vals
        ):
            return

        for line in self:
            if line.move_id.state != 'posted':
                continue

            current_distribution = (
                line.analytic_distribution
                or {}
            )

            new_distribution = (
                vals.get(
                    'analytic_distribution'
                )
                if analytic_in_vals
                else current_distribution
            ) or {}

            current_branch_id = (
                line.branch_id.id
                if line.branch_id
                else False
            )

            new_branch_id = (
                vals.get('branch_id')
                if branch_in_vals
                else current_branch_id
            ) or False

            analytic_changed = (
                analytic_in_vals
                and self._analytic_distribution_changed(
                    current_distribution,
                    new_distribution
                )
            )

            branch_changed = (
                branch_in_vals
                and new_branch_id
                != current_branch_id
            )

            if (
                not analytic_changed
                and not branch_changed
            ):
                continue

            current_data = (
                self._get_analytic_branch_data(
                    current_distribution
                )
            )

            if current_data['shared_analytics']:
                raise ValidationError(
                    _(
                        'You cannot modify the analytic distribution '
                        'or branch of this posted journal item because '
                        'it contains a shared analytic account.'
                    )
                )

            new_data = (
                self._get_analytic_branch_data(
                    new_distribution
                )
            )

            if not new_data['analytics']:
                continue

            if new_data['shared_analytics']:
                raise ValidationError(
                    _(
                        'You cannot assign a shared analytic account '
                        'to a posted journal entry.'
                    )
                )

            if new_data['analytics_without_branch']:
                raise ValidationError(
                    _(
                        'The selected analytic account has no branch '
                        'configuration.'
                    )
                )

            analytic_branches = (
                new_data['branches']
            )

            if len(analytic_branches) > 1:
                raise ValidationError(
                    _(
                        'The selected analytic accounts point to '
                        'different branches, so this posted journal '
                        'item cannot be updated.'
                    )
                )

            if len(analytic_branches) != 1:
                continue

            required_branch = (
                analytic_branches[0]
            )

            if (
                new_branch_id
                != required_branch.id
            ):
                raise ValidationError(
                    _(
                        'The journal-item branch must match the '
                        'branch for the analytic account.'
                    )
                )

    @api.model
    def _prepare_product_tag_vals(self, vals):
        vals = dict(vals or {})

        if 'product_id' not in vals:
            return vals

        product_id = vals.get(
            'product_id'
        )

        if not product_id:
            vals['product_tag_id'] = False
            return vals

        product = self.env['product.product'].browse(
            product_id
        ).exists()

        tag = (
            product.product_tmpl_id.product_tag_ids[:1]
            if product
            else False
        )

        vals['product_tag_id'] = (
            tag.id
            if tag
            else False
        )

        return vals

    @api.onchange('product_id')
    def _onchange_product_id_set_product_tag_id(self):
        for line in self:
            if not line.product_id:
                line.product_tag_id = False
                continue

            tag = line.product_id.product_tmpl_id.product_tag_ids[:1]

            line.product_tag_id = (
                tag.id
                if tag
                else False
            )

    @api.model_create_multi
    def create(self, vals_list):
        fixed_vals_list = []

        for vals in vals_list:
            vals = dict(vals or {})

            vals = self._prepare_product_tag_vals(
                vals
            )

            if not self.env.context.get(
                'skip_move_branch_default'
            ):
                move_id = vals.get(
                    'move_id'
                )

                if move_id:
                    move = self.env[
                        'account.move'
                    ].browse(
                        move_id
                    ).exists()

                    if (
                        move
                        and move.branch_id
                    ):
                        vals['branch_id'] = (
                            move.branch_id.id
                        )

            if self.env.context.get(
                'fix_landed_cost_amount_currency'
            ):
                vals = (
                    self
                    ._fix_landed_cost_amount_currency_vals(
                        vals
                    )
                )

            fixed_vals_list.append(vals)

        lines = super().create(
            fixed_vals_list
        )

        if self.env.context.get(
            'skip_reconciliation_branch_distribution'
        ):
            return lines

        pnl_account_types = (
            'income',
            'income_other',
            'expense',
            'expense_depreciation',
            'expense_direct_cost',
        )

        lines_to_distribute = lines.filtered(
            lambda line:
                line.move_id.statement_line_id
                and line.account_id.account_type
                in pnl_account_types
                and line.analytic_distribution
                and not line.is_branch_distribution_line
                and line.display_type
                in (
                    False,
                    'product',
                )
        )

        for line in lines_to_distribute:
            line.move_id.with_context(
                skip_reconciliation_branch_distribution=True,
                check_move_validity=False,
                skip_account_move_synchronization=True,
                skip_move_branch_default=True,
                skip_posted_analytic_branch_check=True,
            ).apply_branch_distribution(
                line
            )

        return lines

    def write(self, vals):
        vals = dict(vals or {})

        if (
            'product_id' in vals
            and 'product_tag_id' not in vals
        ):
            vals = self._prepare_product_tag_vals(
                vals
            )

        protected_fields = {
            'analytic_distribution',
            'branch_id',
        }

        if (
            not protected_fields.intersection(
                vals.keys()
            )
            or self.env.context.get(
                'skip_posted_analytic_branch_check'
            )
        ):
            return super().write(vals)

        if len(self) == 1:
            prepared_vals = (
                self._prepare_posted_analytic_branch_vals(
                    self,
                    vals
                )
            )

            self._check_posted_analytic_branch_update(
                prepared_vals
            )

            return super().write(
                prepared_vals
            )

        result = True

        for line in self:
            prepared_vals = (
                line._prepare_posted_analytic_branch_vals(
                    line,
                    vals
                )
            )

            line._check_posted_analytic_branch_update(
                prepared_vals
            )

            line_result = super(
                AccountMoveLineInherit,
                line
            ).write(
                prepared_vals
            )

            result = (
                line_result
                and result
            )

        return result

    @api.constrains(
        'account_id',
        'analytic_distribution',
        'move_id'
    )
    def _check_pnl_analytic_on_bank_reconciliation(
        self
    ):
        pnl_account_types = (
            'income',
            'income_other',
            'expense',
            'expense_depreciation',
            'expense_direct_cost',
        )

        for line in self:
            if (
                line.move_id.statement_line_id
                and line.account_id.account_type
                in pnl_account_types
                and not line.analytic_distribution
                and not line.is_branch_distribution_line
                and line.display_type
                in (
                    False,
                    'product',
                )
            ):
                raise ValidationError(
                    _(
                        'Analytic Distribution is required '
                        'for P&L accounts:\n- %s'
                    ) % (
                        line.account_id.display_name
                    )
                )