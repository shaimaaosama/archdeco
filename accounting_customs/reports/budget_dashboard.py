# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools


class AccountReportBudgetDashboard(models.Model):
    _inherit = 'account.report.budget'

    allowed_user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='account_report_budget_allowed_user_rel',
        column1='budget_id',
        column2='user_id',
        string='Allowed Users',
        tracking=True,
        domain=[('active', '=', True)],
        help='Only selected users can access this budget.',
    )

    @api.model
    def _get_allowed_budget_domain(self):
        return [
            ('allowed_user_ids', 'in', [self.env.user.id]),
        ]

    @api.model
    def _get_allowed_budget(self, budget_id):
        if not budget_id:
            return self.browse()

        return self.search(
            [
                ('id', '=', int(budget_id)),
            ] + self._get_allowed_budget_domain(),
            limit=1,
        )

    @api.model
    def action_open_budget_dashboard(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'account_budget_dashboard',
            'name': _('Budget Dashboard'),
        }

    @api.model
    def _dashboard_float(self, amount):
        return round(amount or 0.0, 2)

    @api.model
    def _is_sales_budget_group(self, budget_group):
        if not budget_group:
            return False

        return (
            (budget_group.name or '').strip().lower()
            == 'sales'
        )

    @api.model
    def _get_budget_period_ratio(self, budget, date_from, date_to):
        if not budget.start_date or not budget.end_date:
            return 0.0

        today = fields.Date.context_today(self)

        period_start = max(
            budget.start_date,
            date_from
        )

        period_end = min(
            budget.end_date,
            date_to
        )

        if period_start > period_end:
            return 0.0

        if period_start > today:
            return 0.0

        effective_end = min(
            period_end,
            today
        )

        if effective_end < period_start:
            return 0.0

        total_budget_days = (
            budget.end_date
            - budget.start_date
        ).days + 1

        selected_elapsed_days = (
            effective_end
            - period_start
        ).days + 1

        if total_budget_days <= 0:
            return 0.0

        selected_elapsed_days = max(
            0,
            min(
                selected_elapsed_days,
                total_budget_days
            )
        )

        return (
            selected_elapsed_days
            / total_budget_days
        )

    @api.model
    def _get_ubr_amount(
        self,
        branch_ids=False,
        date_from=False,
        date_to=False,
        cache=None
    ):
        branch_key = tuple(sorted([
            int(branch_id)
            for branch_id in (branch_ids or [])
            if branch_id
        ]))

        date_from_key = (
            fields.Date.to_string(
                fields.Date.to_date(date_from)
            )
            if date_from
            else False
        )

        date_to_key = (
            fields.Date.to_string(
                fields.Date.to_date(date_to)
            )
            if date_to
            else False
        )

        cache_key = (
            branch_key,
            date_from_key,
            date_to_key
        )

        if cache is not None and cache_key in cache:
            return cache[cache_key]

        if branch_ids is not False and not branch_key:
            if cache is not None:
                cache[cache_key] = 0.0

            return 0.0

        amount = self._get_ubr_amount_cached(
            branch_key,
            date_from_key,
            date_to_key
        )

        if cache is not None:
            cache[cache_key] = amount

        return amount

    @tools.ormcache(
        'self.env.uid',
        'branch_key',
        'date_from_key',
        'date_to_key'
    )
    def _get_ubr_amount_cached(
        self,
        branch_key,
        date_from_key,
        date_to_key
    ):
        filters = {
            'project_ids': [],
            'status_ids': [],
            'branch_ids': list(branch_key),
            'partner_ids': [],
            'date_from': date_from_key,
            'date_to': date_to_key,
        }

        dashboard_data = (
            self.env['project.status.ubr.dashboard']
            .get_dashboard_data(filters)
        )

        return self._dashboard_float(
            dashboard_data.get(
                'totals',
                {}
            ).get(
                'ubr',
                0.0
            )
        )

    @api.model
    def _get_budget_branch_ids(self, budget):
        branch_ids = set()

        if budget.branch_id:
            branch_ids.update(
                budget.branch_id.ids
            )

        if budget.included_branch_ids:
            branch_ids.update(
                budget.included_branch_ids.ids
            )

        return list(branch_ids)

    @api.model
    def _get_budgets_branch_ids(self, budgets):
        branch_ids = set()

        for budget in budgets:
            branch_ids.update(
                self._get_budget_branch_ids(
                    budget
                )
            )

        return list(branch_ids)

    @api.model
    def _get_budget_group_account_types(self, budget_group_ids):
        result = {}

        if not budget_group_ids:
            return result

        accounts = self.env['account.account'].search([
            (
                'budget_group_id',
                'in',
                budget_group_ids
            ),
        ])

        for account in accounts:
            if not account.budget_group_id:
                continue

            result.setdefault(
                account.budget_group_id.id,
                set()
            ).add(
                account.account_type
            )

        return result

    @api.model
    def _get_amount_from_account_balance(self, account, budget_group, balance):
        if self._is_sales_budget_group(
            budget_group
        ):
            return -balance

        if account.account_type in (
            'income',
            'income_other',
            'expense',
            'expense_direct_cost',
            'expense_depreciation',
        ):
            return -balance

        return balance

    @api.model
    def _get_actual_amount_map(
        self,
        date_from,
        date_to,
        budget_group_ids,
        branch_ids
    ):
        actual_map = {}

        if not budget_group_ids or not branch_ids:
            return actual_map

        domain = [
            (
                'account_id.budget_group_id',
                'in',
                budget_group_ids
            ),
            (
                'branch_id',
                'in',
                branch_ids
            ),
            (
                'date',
                '>=',
                date_from
            ),
            (
                'date',
                '<=',
                date_to
            ),
            (
                'move_id.state',
                '=',
                'posted'
            ),
            (
                'display_type',
                'not in',
                (
                    'line_section',
                    'line_note'
                )
            ),
        ]

        grouped_data = self.env['account.move.line'].read_group(
            domain=domain,
            fields=[
                'balance:sum',
                'account_id',
                'branch_id',
            ],
            groupby=[
                'account_id',
                'branch_id',
            ],
            lazy=False,
        )

        account_ids = [
            row['account_id'][0]
            for row in grouped_data
            if row.get('account_id')
        ]

        accounts_by_id = {
            account.id: account
            for account in self.env['account.account'].browse(account_ids)
        }

        for row in grouped_data:
            account_data = row.get(
                'account_id'
            )

            branch_data = row.get(
                'branch_id'
            )

            if not account_data or not branch_data:
                continue

            account = accounts_by_id.get(
                account_data[0]
            )

            if (
                not account
                or not account.budget_group_id
            ):
                continue

            budget_group = account.budget_group_id

            balance = (
                row.get(
                    'balance',
                    0.0
                )
                or 0.0
            )

            amount = self._get_amount_from_account_balance(
                account,
                budget_group,
                balance
            )

            key = (
                budget_group.id,
                branch_data[0]
            )

            actual_map[key] = (
                actual_map.get(
                    key,
                    0.0
                )
                + amount
            )

        return actual_map

    @api.model
    def _get_cinema_branch_configs(self):
        cinema_branches = self.env['res.branch'].search([
            ('is_cinema_branch', '=', True),
        ])

        configs = []

        for branch in cinema_branches:
            tag_ids = branch.cinema_product_tag_ids.ids

            if not tag_ids:
                continue

            configs.append({
                'branch_id': branch.id,
                'tag_ids': set(tag_ids),
            })

        return configs

    @api.model
    def _get_cinema_product_amount_map(
        self,
        date_from,
        date_to,
        budget_group_ids
    ):
        amount_map = {}
        detail_map = {}

        if not budget_group_ids:
            return amount_map, detail_map

        cinema_configs = self._get_cinema_branch_configs()

        if not cinema_configs:
            return amount_map, detail_map

        cinema_branch_ids = {
            config['branch_id']
            for config in cinema_configs
        }

        cinema_tag_ids = set()

        for config in cinema_configs:
            cinema_tag_ids.update(
                config['tag_ids']
            )

        if not cinema_tag_ids:
            return amount_map, detail_map

        has_line_product_tag = (
            'product_tag_id'
            in self.env['account.move.line']._fields
        )

        domain = [
            (
                'account_id.budget_group_id',
                'in',
                budget_group_ids
            ),
            (
                'date',
                '>=',
                date_from
            ),
            (
                'date',
                '<=',
                date_to
            ),
            (
                'move_id.state',
                '=',
                'posted'
            ),
            (
                'display_type',
                'not in',
                (
                    'line_section',
                    'line_note'
                )
            ),
            (
                'branch_id',
                '!=',
                False
            ),
            (
                'branch_id',
                'not in',
                list(cinema_branch_ids)
            ),
        ]

        if has_line_product_tag:
            domain += [
                '|',
                (
                    'product_id.product_tmpl_id.product_tag_ids',
                    'in',
                    list(cinema_tag_ids)
                ),
                (
                    'product_tag_id',
                    'in',
                    list(cinema_tag_ids)
                ),
            ]
        else:
            domain += [
                (
                    'product_id.product_tmpl_id.product_tag_ids',
                    'in',
                    list(cinema_tag_ids)
                ),
            ]

        fields_list = [
            'balance:sum',
            'account_id',
            'branch_id',
            'product_id',
        ]

        groupby_list = [
            'account_id',
            'branch_id',
            'product_id',
        ]

        if has_line_product_tag:
            fields_list.append(
                'product_tag_id'
            )

            groupby_list.append(
                'product_tag_id'
            )

        grouped_data = self.env['account.move.line'].read_group(
            domain=domain,
            fields=fields_list,
            groupby=groupby_list,
            lazy=False,
        )

        account_ids = [
            row['account_id'][0]
            for row in grouped_data
            if row.get('account_id')
        ]

        branch_ids = [
            row['branch_id'][0]
            for row in grouped_data
            if row.get('branch_id')
        ]

        product_ids = [
            row['product_id'][0]
            for row in grouped_data
            if row.get('product_id')
        ]

        accounts_by_id = {
            account.id: account
            for account in self.env['account.account'].browse(account_ids)
        }

        branches_by_id = {
            branch.id: branch
            for branch in self.env['res.branch'].browse(branch_ids)
        }

        products_by_id = {
            product.id: product
            for product in self.env['product.product'].browse(product_ids)
        }

        for row in grouped_data:
            account_data = row.get(
                'account_id'
            )

            branch_data = row.get(
                'branch_id'
            )

            product_data = row.get(
                'product_id'
            )

            line_tag_data = (
                row.get(
                    'product_tag_id'
                )
                if has_line_product_tag
                else False
            )

            if not account_data or not branch_data:
                continue

            account = accounts_by_id.get(
                account_data[0]
            )

            source_branch = branches_by_id.get(
                branch_data[0]
            )

            product = (
                products_by_id.get(
                    product_data[0]
                )
                if product_data
                else False
            )

            if (
                not account
                or not account.budget_group_id
                or not source_branch
            ):
                continue

            budget_group = account.budget_group_id
            source_branch_id = source_branch.id

            product_tag_ids = set()

            if product:
                product_tag_ids.update(
                    product.product_tmpl_id.product_tag_ids.ids
                )

            if line_tag_data:
                product_tag_ids.add(
                    line_tag_data[0]
                )

            if not product_tag_ids.intersection(
                cinema_tag_ids
            ):
                continue

            balance = (
                row.get(
                    'balance',
                    0.0
                )
                or 0.0
            )

            normal_amount = self._get_amount_from_account_balance(
                account,
                budget_group,
                balance
            )

            for config in cinema_configs:
                if not product_tag_ids.intersection(
                    config['tag_ids']
                ):
                    continue

                cinema_branch_id = config['branch_id']

                cinema_key = (
                    budget_group.id,
                    cinema_branch_id
                )

                amount_map[cinema_key] = (
                    amount_map.get(
                        cinema_key,
                        0.0
                    )
                    + normal_amount
                )

                detail_key = (
                    budget_group.id,
                    cinema_branch_id,
                    source_branch_id
                )

                detail_map[detail_key] = {
                    'branch_id': source_branch_id,
                    'branch_name': source_branch.display_name,
                    'amount': (
                        detail_map.get(
                            detail_key,
                            {}
                        ).get(
                            'amount',
                            0.0
                        )
                        + normal_amount
                    ),
                }

                source_key = (
                    budget_group.id,
                    source_branch_id
                )

                amount_map[source_key] = (
                    amount_map.get(
                        source_key,
                        0.0
                    )
                    - normal_amount
                )

        return amount_map, detail_map

    @api.model
    def _get_budget_line_status_from_types(self, account_types, difference):
        is_income = any(
            account_type in (
                'income',
                'income_other',
            )
            for account_type in account_types
        )

        is_expense = any(
            account_type in (
                'expense',
                'expense_direct_cost',
                'expense_depreciation',
            )
            for account_type in account_types
        )

        return (
            bool(
                is_income
                and difference < 0
            ),
            bool(
                is_expense
                and difference < 0
            ),
        )

    @api.model
    def _get_dashboard_budget_amounts_bulk(
        self,
        budgets,
        date_from,
        date_to,
        include_lines=False
    ):
        result = {}

        if not budgets:
            return result

        budget_group_ids = list(set(
            budgets.mapped(
                'budget_line_ids.budget_group_id'
            ).ids
        ))

        all_branch_ids = set()

        for budget in budgets:
            all_branch_ids.update(
                budget.branch_id.ids
            )

            all_branch_ids.update(
                budget.included_branch_ids.ids
            )

        actual_map = self._get_actual_amount_map(
            date_from,
            date_to,
            budget_group_ids,
            list(all_branch_ids)
        )

        if include_lines:
            (
                cinema_amount_map,
                cinema_detail_map,
            ) = self._get_cinema_product_amount_map(
                date_from,
                date_to,
                budget_group_ids
            )
        else:
            cinema_amount_map = {}
            cinema_detail_map = {}

        group_account_types = (
            self._get_budget_group_account_types(
                budget_group_ids
            )
        )

        for budget in budgets:
            ratio = self._get_budget_period_ratio(
                budget,
                date_from,
                date_to
            )

            budget_branch_ids = list(set(
                budget.branch_id.ids
                + budget.included_branch_ids.ids
            ))

            is_cinema_budget_branch = bool(
                budget.branch_id
                and budget.branch_id.is_cinema_branch
            )

            planned = 0.0
            theoretical = 0.0
            actual = 0.0
            difference = 0.0

            total_planned_sales = 0.0
            period_planned_sales = 0.0
            actual_sales = 0.0
            sales_difference = 0.0
            total_cinema_products_amount = 0.0

            line_rows = []

            for line in budget.budget_line_ids:
                if not line.budget_group_id:
                    continue

                budget_group = line.budget_group_id
                group_id = budget_group.id

                line_planned = (
                    line.planned_amount
                    or 0.0
                )

                line_theoretical = (
                    line_planned
                    * ratio
                )

                line_actual = sum(
                    actual_map.get(
                        (
                            group_id,
                            branch_id
                        ),
                        0.0
                    )
                    for branch_id
                    in budget_branch_ids
                )

                line_difference = (
                    line_theoretical
                    - line_actual
                )

                line_cinema_products_amount = sum(
                    cinema_amount_map.get(
                        (
                            group_id,
                            branch_id
                        ),
                        0.0
                    )
                    for branch_id
                    in budget_branch_ids
                )

                line_cinema_products_details = []

                if is_cinema_budget_branch:
                    detail_rows = [
                        detail
                        for key, detail in cinema_detail_map.items()
                        if (
                            key[0] == group_id
                            and key[1] in budget_branch_ids
                        )
                    ]

                    for detail in detail_rows:
                        line_cinema_products_details.append({
                            'branch_id': detail.get(
                                'branch_id'
                            ),
                            'branch_name': detail.get(
                                'branch_name'
                            ),
                            'amount': self._dashboard_float(
                                detail.get(
                                    'amount',
                                    0.0
                                )
                            ),
                        })

                is_sales_line = (
                    self._is_sales_budget_group(
                        budget_group
                    )
                )

                line_total_planned_sales = (
                    line_planned
                    if is_sales_line
                    else 0.0
                )

                line_period_planned_sales = (
                    line_theoretical
                    if is_sales_line
                    else 0.0
                )

                line_actual_sales = (
                    line_actual
                    if is_sales_line
                    else 0.0
                )

                line_sales_difference = (
                    line_period_planned_sales
                    - line_actual_sales
                )

                planned += line_planned
                theoretical += line_theoretical
                actual += line_actual
                difference += line_difference

                total_planned_sales += (
                    line_total_planned_sales
                )

                period_planned_sales += (
                    line_period_planned_sales
                )

                actual_sales += (
                    line_actual_sales
                )

                sales_difference += (
                    line_sales_difference
                )

                total_cinema_products_amount += (
                    line_cinema_products_amount
                )

                if include_lines:
                    account_types = (
                        group_account_types.get(
                            group_id,
                            set()
                        )
                    )

                    (
                        is_over_target,
                        is_over_budget,
                    ) = (
                        self
                        ._get_budget_line_status_from_types(
                            account_types,
                            line_difference
                        )
                    )

                    line_rows.append({
                        'id': line.id,
                        'budget_group_id': (
                            group_id
                        ),
                        'budget_group_name': (
                            budget_group.display_name
                        ),
                        'planned': (
                            self._dashboard_float(
                                line_planned
                            )
                        ),
                        'theoretical': (
                            self._dashboard_float(
                                line_theoretical
                            )
                        ),
                        'actual': (
                            self._dashboard_float(
                                line_actual
                            )
                        ),
                        'difference': (
                            self._dashboard_float(
                                line_difference
                            )
                        ),
                        'sales': (
                            self._dashboard_float(
                                line_actual_sales
                            )
                        ),
                        'cinema_products_amount': (
                            self._dashboard_float(
                                line_cinema_products_amount
                            )
                        ),
                        'cinema_products_details': (
                            line_cinema_products_details
                        ),
                        'can_open_cinema_products': bool(
                            is_cinema_budget_branch
                            and line_cinema_products_details
                        ),
                        'is_sales': (
                            is_sales_line
                        ),
                        'is_over_budget': (
                            is_over_budget
                        ),
                        'is_over_target': (
                            is_over_target
                        ),
                    })

            result[budget.id] = {
                'planned': (
                    self._dashboard_float(
                        planned
                    )
                ),
                'theoretical': (
                    self._dashboard_float(
                        theoretical
                    )
                ),
                'actual': (
                    self._dashboard_float(
                        actual
                    )
                ),
                'difference': (
                    self._dashboard_float(
                        difference
                    )
                ),
                'sales': (
                    self._dashboard_float(
                        actual_sales
                    )
                ),
                'total_planned_sales': (
                    self._dashboard_float(
                        total_planned_sales
                    )
                ),
                'period_planned_sales': (
                    self._dashboard_float(
                        period_planned_sales
                    )
                ),
                'actual_sales': (
                    self._dashboard_float(
                        actual_sales
                    )
                ),
                'sales_difference': (
                    self._dashboard_float(
                        sales_difference
                    )
                ),
                'cinema_products_amount': (
                    self._dashboard_float(
                        total_cinema_products_amount
                    )
                ),
                'show_cinema_products': bool(
                    total_cinema_products_amount
                ),
                'is_cinema_branch': (
                    is_cinema_budget_branch
                ),
                'lines': line_rows,
            }

        return result

    @api.model
    def get_budget_dashboard_years(self):
        budgets = self.search(
            self._get_allowed_budget_domain() + [
                (
                    'start_date',
                    '!=',
                    False
                ),
                (
                    'end_date',
                    '!=',
                    False
                ),
            ],
            order='start_date asc, id asc',
        )

        years_set = set()

        for budget in budgets:
            for year in range(
                budget.start_date.year,
                budget.end_date.year + 1
            ):
                years_set.add(year)

        result = []
        ubr_cache = {}

        for year in sorted(years_set):
            date_from = fields.Date.to_date(
                '%s-01-01' % year
            )

            date_to = fields.Date.to_date(
                '%s-12-31' % year
            )

            year_budgets = budgets.filtered(
                lambda budget:
                    budget.start_date <= date_to
                    and budget.end_date >= date_from
            )

            amount_by_budget = (
                self
                ._get_dashboard_budget_amounts_bulk(
                    year_budgets,
                    date_from,
                    date_to,
                    include_lines=False
                )
            )

            planned = 0.0
            actual = 0.0
            sales = 0.0

            for budget in year_budgets:
                amounts = amount_by_budget.get(
                    budget.id,
                    {}
                )

                planned += amounts.get(
                    'planned',
                    0.0
                )

                actual += amounts.get(
                    'actual',
                    0.0
                )

                sales += amounts.get(
                    'actual_sales',
                    0.0
                )

            ubr = self._get_ubr_amount(
                branch_ids=self._get_budgets_branch_ids(
                    year_budgets
                ),
                date_from=False,
                date_to=False,
                cache=ubr_cache
            )

            result.append({
                'year': year,
                'budget_count': len(
                    year_budgets
                ),
                'planned': (
                    self._dashboard_float(
                        planned
                    )
                ),
                'actual': (
                    self._dashboard_float(
                        actual
                    )
                ),
                'ubr': (
                    self._dashboard_float(
                        ubr
                    )
                ),
                'sales': (
                    self._dashboard_float(
                        sales
                    )
                ),
                'difference': (
                    self._dashboard_float(
                        planned - actual
                    )
                ),
            })

        return result

    @api.model
    def _get_year_budget_records(
        self,
        year,
        date_from=False,
        date_to=False,
        budget_ids=False
    ):
        year = int(year)

        year_date_from = fields.Date.to_date(
            '%s-01-01' % year
        )

        year_date_to = fields.Date.to_date(
            '%s-12-31' % year
        )

        date_from = (
            fields.Date.to_date(date_from)
            if date_from
            else year_date_from
        )

        date_to = (
            fields.Date.to_date(date_to)
            if date_to
            else year_date_to
        )

        available_budgets = self.search(
            self._get_allowed_budget_domain() + [
                (
                    'start_date',
                    '<=',
                    year_date_to
                ),
                (
                    'end_date',
                    '>=',
                    year_date_from
                ),
            ],
            order='name asc, id asc',
        )

        period_budgets = (
            available_budgets.filtered(
                lambda budget:
                    budget.start_date <= date_to
                    and budget.end_date >= date_from
            )
        )

        if (
            budget_ids is False
            or budget_ids is None
        ):
            selected_budget_ids = set(
                available_budgets.ids
            )
        else:
            selected_budget_ids = {
                int(budget_id)
                for budget_id in budget_ids
                if budget_id
            }

        budgets = period_budgets.filtered(
            lambda budget:
                budget.id in selected_budget_ids
        )

        return (
            year,
            date_from,
            date_to,
            available_budgets,
            budgets,
            selected_budget_ids
        )

    @api.model
    def get_budget_dashboard_year_details(
        self,
        year,
        date_from=False,
        date_to=False,
        budget_ids=False
    ):
        (
            year,
            date_from,
            date_to,
            available_budgets,
            budgets,
            selected_budget_ids
        ) = self._get_year_budget_records(
            year,
            date_from=date_from,
            date_to=date_to,
            budget_ids=budget_ids
        )

        available_budget_rows = [
            {
                'id': budget.id,
                'name': budget.display_name,
                'branch_name': (
                    budget.branch_id.display_name
                    or _('No Branch')
                ),
            }
            for budget in available_budgets
        ]

        amount_by_budget = (
            self
            ._get_dashboard_budget_amounts_bulk(
                budgets,
                date_from,
                date_to,
                include_lines=False
            )
        )

        total_planned = 0.0
        total_theoretical = 0.0
        total_actual = 0.0
        total_difference = 0.0

        total_planned_sales = 0.0
        total_period_planned_sales = 0.0
        total_actual_sales = 0.0
        total_sales_difference = 0.0

        budget_rows = []

        for budget in budgets:
            amounts = amount_by_budget.get(
                budget.id,
                {}
            )

            planned = amounts.get(
                'planned',
                0.0
            )

            theoretical = amounts.get(
                'theoretical',
                0.0
            )

            actual = amounts.get(
                'actual',
                0.0
            )

            difference = amounts.get(
                'difference',
                0.0
            )

            planned_sales = amounts.get(
                'total_planned_sales',
                0.0
            )

            period_planned_sales = amounts.get(
                'period_planned_sales',
                0.0
            )

            actual_sales = amounts.get(
                'actual_sales',
                0.0
            )

            sales_difference = amounts.get(
                'sales_difference',
                0.0
            )

            total_planned += planned
            total_theoretical += theoretical
            total_actual += actual
            total_difference += difference

            total_planned_sales += (
                planned_sales
            )

            total_period_planned_sales += (
                period_planned_sales
            )

            total_actual_sales += (
                actual_sales
            )

            total_sales_difference += (
                sales_difference
            )

            budget_rows.append({
                'id': budget.id,
                'name': budget.display_name,
                'branch_id': (
                    budget.branch_id.id
                ),
                'branch_name': (
                    budget.branch_id.display_name
                    or _('No Branch')
                ),
                'planned': (
                    self._dashboard_float(
                        planned
                    )
                ),
                'theoretical': (
                    self._dashboard_float(
                        theoretical
                    )
                ),
                'sales': (
                    self._dashboard_float(
                        actual_sales
                    )
                ),
                'total_planned_sales': (
                    self._dashboard_float(
                        planned_sales
                    )
                ),
                'period_planned_sales': (
                    self._dashboard_float(
                        period_planned_sales
                    )
                ),
                'actual_sales': (
                    self._dashboard_float(
                        actual_sales
                    )
                ),
                'sales_difference': (
                    self._dashboard_float(
                        sales_difference
                    )
                ),
                'actual': (
                    self._dashboard_float(
                        actual
                    )
                ),
                'ubr': 0.0,
                'difference': (
                    self._dashboard_float(
                        difference
                    )
                ),
            })

        branch_count = len(set(
            row['branch_id']
            for row in budget_rows
            if row.get('branch_id')
        ))

        valid_selected_budget_ids = [
            budget.id
            for budget in available_budgets
            if budget.id in selected_budget_ids
        ]

        return {
            'year': year,
            'date_from': str(
                date_from
            ),
            'date_to': str(
                date_to
            ),
            'available_budgets': (
                available_budget_rows
            ),
            'selected_budget_ids': (
                valid_selected_budget_ids
            ),
            'summary': {
                'planned': (
                    self._dashboard_float(
                        total_planned
                    )
                ),
                'theoretical': (
                    self._dashboard_float(
                        total_theoretical
                    )
                ),
                'actual': (
                    self._dashboard_float(
                        total_actual
                    )
                ),
                'difference': (
                    self._dashboard_float(
                        total_difference
                    )
                ),
                'sales': (
                    self._dashboard_float(
                        total_actual_sales
                    )
                ),
                'total_planned_sales': (
                    self._dashboard_float(
                        total_planned_sales
                    )
                ),
                'period_planned_sales': (
                    self._dashboard_float(
                        total_period_planned_sales
                    )
                ),
                'actual_sales': (
                    self._dashboard_float(
                        total_actual_sales
                    )
                ),
                'sales_difference': (
                    self._dashboard_float(
                        total_sales_difference
                    )
                ),
                'ubr': 0.0,
                'budget_count': len(
                    budgets
                ),
                'branch_count': (
                    branch_count
                ),
            },
            'budgets': budget_rows,
        }

    @api.model
    def get_budget_dashboard_year_ubr_values(
        self,
        year,
        date_from=False,
        date_to=False,
        budget_ids=False
    ):
        ubr_date_from = (
            fields.Date.to_date(date_from)
            if date_from
            else False
        )

        ubr_date_to = (
            fields.Date.to_date(date_to)
            if date_to
            else False
        )

        (
            year,
            date_from,
            date_to,
            available_budgets,
            budgets,
            selected_budget_ids
        ) = self._get_year_budget_records(
            year,
            date_from=ubr_date_from,
            date_to=ubr_date_to,
            budget_ids=budget_ids
        )

        ubr_cache = {}
        rows = []

        for budget in budgets:
            ubr = self._get_ubr_amount(
                branch_ids=self._get_budget_branch_ids(
                    budget
                ),
                date_from=ubr_date_from,
                date_to=ubr_date_to,
                cache=ubr_cache
            )

            rows.append({
                'id': budget.id,
                'ubr': self._dashboard_float(
                    ubr
                ),
            })

        summary_ubr = self._get_ubr_amount(
            branch_ids=self._get_budgets_branch_ids(
                budgets
            ),
            date_from=ubr_date_from,
            date_to=ubr_date_to,
            cache=ubr_cache
        )

        return {
            'year': year,
            'date_from': str(
                date_from
            ),
            'date_to': str(
                date_to
            ),
            'selected_budget_ids': [
                budget.id
                for budget in available_budgets
                if budget.id in selected_budget_ids
            ],
            'summary_ubr': self._dashboard_float(
                summary_ubr
            ),
            'budgets': rows,
        }

    @api.model
    def get_budget_dashboard_budget_details(
        self,
        budget_id,
        date_from,
        date_to,
        use_ubr_dates=False
    ):
        budget = self._get_allowed_budget(
            budget_id
        )

        if not budget:
            return {
                'id': False,
                'included_branches': [],
                'lines': [],
            }

        date_from = fields.Date.to_date(
            date_from
        )

        date_to = fields.Date.to_date(
            date_to
        )

        amount_by_budget = (
            self
            ._get_dashboard_budget_amounts_bulk(
                budget,
                date_from,
                date_to,
                include_lines=True
            )
        )

        amounts = amount_by_budget.get(
            budget.id,
            {}
        )

        ubr = self._get_ubr_amount(
            branch_ids=self._get_budget_branch_ids(
                budget
            ),
            date_from=date_from if use_ubr_dates else False,
            date_to=date_to if use_ubr_dates else False
        )

        return {
            'id': budget.id,
            'name': budget.display_name,
            'branch_name': (
                budget.branch_id.display_name
                or _('No Branch')
            ),
            'is_cinema_branch': bool(
                budget.branch_id
                and budget.branch_id.is_cinema_branch
            ),
            'state': budget.state,
            'start_date': (
                str(budget.start_date)
                if budget.start_date
                else False
            ),
            'end_date': (
                str(budget.end_date)
                if budget.end_date
                else False
            ),
            'selected_date_from': str(
                date_from
            ),
            'selected_date_to': str(
                date_to
            ),
            'included_branches': (
                budget.included_branch_ids
                .mapped('display_name')
            ),
            'planned': amounts.get(
                'planned',
                0.0
            ),
            'theoretical': amounts.get(
                'theoretical',
                0.0
            ),
            'actual': amounts.get(
                'actual',
                0.0
            ),
            'difference': amounts.get(
                'difference',
                0.0
            ),
            'sales': amounts.get(
                'actual_sales',
                0.0
            ),
            'total_planned_sales': amounts.get(
                'total_planned_sales',
                0.0
            ),
            'period_planned_sales': amounts.get(
                'period_planned_sales',
                0.0
            ),
            'actual_sales': amounts.get(
                'actual_sales',
                0.0
            ),
            'sales_difference': amounts.get(
                'sales_difference',
                0.0
            ),
            'ubr': (
                self._dashboard_float(
                    ubr
                )
            ),
            'cinema_products_amount': amounts.get(
                'cinema_products_amount',
                0.0
            ),
            'show_cinema_products': amounts.get(
                'show_cinema_products',
                False
            ),
            'lines': amounts.get(
                'lines',
                []
            ),
        }

    @api.model
    def action_open_cinema_product_journal_items(
        self,
        budget_id,
        budget_group_id,
        source_branch_id,
        date_from,
        date_to
    ):
        budget = self._get_allowed_budget(
            budget_id
        )

        if not budget:
            return False

        if (
            not budget.branch_id
            or not budget.branch_id.is_cinema_branch
        ):
            return False

        cinema_tag_ids = (
            budget.branch_id
            .cinema_product_tag_ids
            .ids
        )

        if not cinema_tag_ids:
            return False

        date_from_obj = fields.Date.to_date(
            date_from
        )

        date_to_obj = fields.Date.to_date(
            date_to
        )

        has_line_product_tag = (
            'product_tag_id'
            in self.env['account.move.line']._fields
        )

        domain = [
            (
                'account_id.budget_group_id',
                '=',
                int(budget_group_id)
            ),
            (
                'branch_id',
                '=',
                int(source_branch_id)
            ),
            (
                'date',
                '>=',
                date_from_obj
            ),
            (
                'date',
                '<=',
                date_to_obj
            ),
            (
                'move_id.state',
                '=',
                'posted'
            ),
            (
                'display_type',
                'not in',
                (
                    'line_section',
                    'line_note'
                )
            ),
        ]

        if has_line_product_tag:
            domain += [
                '|',
                (
                    'product_id.product_tmpl_id.product_tag_ids',
                    'in',
                    cinema_tag_ids
                ),
                (
                    'product_tag_id',
                    'in',
                    cinema_tag_ids
                ),
            ]
        else:
            domain += [
                (
                    'product_id.product_tmpl_id.product_tag_ids',
                    'in',
                    cinema_tag_ids
                ),
            ]

        branch = self.env['res.branch'].browse(
            int(source_branch_id)
        ).exists()

        budget_group = self.env['budget.group'].browse(
            int(budget_group_id)
        ).exists()

        action_name = (
            '%s - Cinema Products - %s'
            % (
                budget.branch_id.display_name,
                branch.display_name or ''
            )
        )

        if budget_group:
            action_name = (
                '%s - %s'
                % (
                    action_name,
                    budget_group.display_name
                )
            )

        list_view = self.env.ref(
            (
                'accounting_customs.'
                'view_budget_dashboard_move_line_list'
            ),
            raise_if_not_found=False
        )

        views = [
            (
                list_view.id,
                'list'
            )
            if list_view
            else (
                False,
                'list'
            ),
            (
                False,
                'form'
            ),
        ]

        return {
            'type': 'ir.actions.act_window',
            'name': action_name,
            'res_model': 'account.move.line',
            'views': views,
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'search_default_group_by_date_month': 1,
                'search_default_group_by_account_id': 1,
                'from_budget_dashboard': True,
                'budget_dashboard_budget_id': budget.id,
                'budget_dashboard_year': date_from_obj.year,
                'budget_dashboard_date_from': str(date_from_obj),
                'budget_dashboard_date_to': str(date_to_obj),
                'create': False,
                'edit': False,
                'delete': False,
                'import': False,
            },
            'target': 'current',
        }

    @api.model
    def action_open_budget_line_actual_move_lines(
        self,
        budget_line_id,
        date_from,
        date_to
    ):
        line = self.env[
            'account.budget.line'
        ].browse(
            int(budget_line_id)
        ).exists()

        if not line:
            return False

        budget = self._get_allowed_budget(
            line.budget_id.id
        )

        if not budget:
            return False

        branch_ids = list(set(
            budget.branch_id.ids
            + budget.included_branch_ids.ids
        ))

        date_from_obj = fields.Date.to_date(
            date_from
        )

        date_to_obj = fields.Date.to_date(
            date_to
        )

        domain = [
            (
                'account_id.budget_group_id',
                '=',
                line.budget_group_id.id
            ),
            (
                'branch_id',
                'in',
                branch_ids
            ),
            (
                'date',
                '>=',
                date_from_obj
            ),
            (
                'date',
                '<=',
                date_to_obj
            ),
            (
                'move_id.state',
                '=',
                'posted'
            ),
            (
                'display_type',
                'not in',
                (
                    'line_section',
                    'line_note'
                )
            ),
        ]

        group_name = (
            line.budget_group_id.display_name
            or ''
        )

        if ' - ' in group_name:
            group_name = group_name.split(
                ' - ',
                1
            )[1]

        action_name = (
            '%s - %s - %s - %s'
            % (
                (
                    budget.branch_id.display_name
                    or ''
                ),
                group_name,
                date_from_obj.strftime(
                    '%m-%d-%Y'
                ),
                date_to_obj.strftime(
                    '%m-%d-%Y'
                ),
            )
        )

        list_view = self.env.ref(
            (
                'accounting_customs.'
                'view_budget_dashboard_move_line_list'
            ),
            raise_if_not_found=False
        )

        views = [
            (
                list_view.id,
                'list'
            )
            if list_view
        else (
                False,
                'list'
            ),
            (
                False,
                'form'
            ),
        ]

        return {
            'type': 'ir.actions.act_window',
            'name': action_name,
            'res_model': 'account.move.line',
            'views': views,
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'search_default_group_by_date_month': 1,
                'search_default_group_by_account_id': 1,
                'from_budget_dashboard': True,
                'budget_dashboard_budget_id': (
                    budget.id
                ),
                'budget_dashboard_year': (
                    date_from_obj.year
                ),
                'budget_dashboard_date_from': (
                    str(date_from_obj)
                ),
                'budget_dashboard_date_to': (
                    str(date_to_obj)
                ),
                'create': False,
                'edit': False,
                'delete': False,
                'import': False,
            },
            'target': 'current',
        }