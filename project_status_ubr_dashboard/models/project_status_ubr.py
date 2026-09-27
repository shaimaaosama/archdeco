import io

import xlsxwriter

from odoo import _, api, models
from odoo.exceptions import UserError


class ProjectStatusUBRDashboard(models.AbstractModel):
    _name = "project.status.ubr.dashboard"
    _description = "Project Status and UBR Dashboard"

    @api.model
    def get_filter_options(self):
        SaleOrder = self.env["sale.order"]

        orders = SaleOrder.search([
            ("project_id", "!=", False),
            ("state", "in", ["sale", "done"]),
        ])

        projects = orders.project_id.sorted(
            lambda project: project.name or ""
        )

        stages = projects.stage_id.sorted(
            lambda stage: stage.name or ""
        )

        partners = orders.partner_id.sorted(
            lambda partner: partner.name or ""
        )

        branch_field = self._get_branch_field()
        branches = []

        if branch_field:
            branch_records = orders.mapped(branch_field)

            branches = [
                {
                    "id": branch.id,
                    "name": branch.name or "",
                }
                for branch in branch_records.sorted(
                    lambda branch: branch.name or ""
                )
            ]

        currency = self.env.company.currency_id

        return {
            "projects": [
                {
                    "id": project.id,
                    "name": project.name or "",
                }
                for project in projects
            ],
            "statuses": [
                {
                    "id": stage.id,
                    "name": stage.name or "",
                }
                for stage in stages
            ],
            "branches": branches,
            "partners": [
                {
                    "id": partner.id,
                    "name": partner.name or "",
                }
                for partner in partners
            ],
            "branch_label": (
                SaleOrder._fields[branch_field].string
                if branch_field
                else _("Branch")
            ),
            "currency": {
                "symbol": currency.symbol,
                "position": currency.position,
                "decimal_places": currency.decimal_places,
            },
        }

    @api.model
    def get_initial_data(self, filters=None):
        filters = filters or {}

        return {
            "options": self.get_filter_options(),
            "data": self.get_dashboard_data(filters),
        }

    @api.model
    def get_dashboard_data(self, filters=None):
        filters = filters or {}

        all_orders = self._get_filtered_orders(
            filters,
            apply_dates=False,
        )

        if not all_orders:
            return {
                "rows": [],
                "totals": self._prepare_totals([]),
                "count": 0,
            }

        projects = all_orders.project_id

        if filters.get("status_ids"):
            status_ids = {
                int(status_id)
                for status_id in filters["status_ids"]
            }

            projects = projects.filtered(
                lambda project: (
                    project.stage_id.id in status_ids
                )
            )

            all_orders = all_orders.filtered(
                lambda order: order.project_id in projects
            )

        projects = projects.sorted(
            lambda project: project.name or ""
        )

        period_orders = self._get_filtered_orders(
            filters,
            apply_dates=True,
        )

        period_orders = period_orders.filtered(
            lambda order: order.project_id in projects
        )

        all_orders_by_project = {
            project.id: self.env["sale.order"]
            for project in projects
        }

        period_orders_by_project = {
            project.id: self.env["sale.order"]
            for project in projects
        }

        for order in all_orders:
            project_id = order.project_id.id

            if project_id in all_orders_by_project:
                all_orders_by_project[project_id] |= order

        for order in period_orders:
            project_id = order.project_id.id

            if project_id in period_orders_by_project:
                period_orders_by_project[project_id] |= order

        analytic_ids_by_project = (
            self._get_analytic_ids_by_project(all_orders)
        )

        journal_amounts_by_project = (
            self._get_bulk_journal_amounts(
                analytic_ids_by_project,
                filters.get("date_from"),
                filters.get("date_to"),
            )
        )

        rows = []

        for project in projects:
            rows.append(
                self._prepare_project_row_bulk(
                    project=project,
                    all_orders=all_orders_by_project[
                        project.id
                    ],
                    period_orders=period_orders_by_project[
                        project.id
                    ],
                    analytic_ids=analytic_ids_by_project.get(
                        project.id,
                        set(),
                    ),
                    journal_amounts=(
                        journal_amounts_by_project.get(
                            project.id,
                            {},
                        )
                    ),
                )
            )

        return {
            "rows": rows,
            "totals": self._prepare_totals(rows),
            "count": len(rows),
        }

    @api.model
    def action_open_journal_items(
        self,
        project_id,
        metric,
        date_from=False,
        date_to=False,
    ):
        project = self.env[
            "project.project"
        ].browse(
            int(project_id)
        ).exists()

        if not project:
            raise UserError(
                _("The selected project no longer exists.")
            )

        orders = self.env["sale.order"].search([
            ("project_id", "=", project.id),
            ("state", "in", ["sale", "done"]),
        ])

        analytic_ids = (
            self._get_order_analytic_accounts(orders).ids
        )

        if not analytic_ids:
            raise UserError(
                _(
                    "No analytic accounts were found "
                    "for project %s."
                )
                % (project.name or "")
            )

        account_ids = self._get_metric_account_ids(
            metric
        )

        if not account_ids:
            raise UserError(
                _(
                    "No related accounts were found "
                    "for this amount."
                )
            )

        journal_item_ids = (
            self._get_journal_item_ids_sql(
                analytic_ids=analytic_ids,
                account_ids=account_ids,
                date_from=date_from,
                date_to=date_to,
            )
        )

        metric_names = {
            "actual_expenses": _("Actual Expenses"),
            "actual_sales": _("Actual Sales"),
            "retention": _("Retention"),
            "down_payment": _("Advance Payment"),
            "lg": _("LG"),
        }

        action_name = "%s - %s" % (
            metric_names.get(
                metric,
                _("Journal Items"),
            ),
            project.name or "",
        )

        list_view = self.env.ref(
            "account.view_move_line_tree",
            raise_if_not_found=False,
        )

        form_view = self.env.ref(
            "account.view_move_line_form",
            raise_if_not_found=False,
        )

        views = [
            (
                list_view.id if list_view else False,
                "list",
            ),
            (
                form_view.id if form_view else False,
                "form",
            ),
        ]

        return {
            "type": "ir.actions.act_window",
            "name": action_name,
            "res_model": "account.move.line",
            "view_mode": "list,form",
            "views": views,
            "domain": [
                (
                    "id",
                    "in",
                    journal_item_ids,
                ),
            ],
            "target": "current",
            "context": {
                "create": False,
                "edit": False,
                "delete": False,
            },
        }

    @api.model
    def get_excel_file(self, filters=None):
        filters = filters or {}

        data = self.get_dashboard_data(filters)

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {
                "in_memory": True,
            },
        )

        worksheet = workbook.add_worksheet(
            "Project Status & UBR"
        )

        self._write_excel_sheet(
            workbook,
            worksheet,
            data,
            filters,
        )

        workbook.close()

        output.seek(0)

        return output.read()

    def _get_filtered_orders(
        self,
        filters,
        apply_dates=False,
    ):
        domain = [
            ("project_id", "!=", False),
            ("state", "in", ["sale", "done"]),
        ]

        if filters.get("project_ids"):
            domain.append(
                (
                    "project_id",
                    "in",
                    filters["project_ids"],
                )
            )

        if filters.get("partner_ids"):
            domain.append(
                (
                    "partner_id",
                    "in",
                    filters["partner_ids"],
                )
            )

        branch_field = self._get_branch_field()

        if branch_field and filters.get("branch_ids"):
            domain.append(
                (
                    branch_field,
                    "in",
                    filters["branch_ids"],
                )
            )

        if apply_dates:
            if filters.get("date_from"):
                domain.append(
                    (
                        "date_order",
                        ">=",
                        filters["date_from"]
                        + " 00:00:00",
                    )
                )

            if filters.get("date_to"):
                domain.append(
                    (
                        "date_order",
                        "<=",
                        filters["date_to"]
                        + " 23:59:59",
                    )
                )

        return self.env["sale.order"].search(domain)

    def _get_project_orders(self, project, filters):
        filters = dict(filters or {})
        filters["project_ids"] = [project.id]

        return self._get_filtered_orders(
            filters,
            apply_dates=bool(
                filters.get("date_from")
                or filters.get("date_to")
            ),
        )

    def _get_branch_field(self):
        fields_map = self.env["sale.order"]._fields

        for field_name in (
            "branch_id",
            "x_branch_id",
        ):
            if field_name in fields_map:
                return field_name

        return False

    def _get_project_analytic_ids(self, project):
        analytic_ids = set()

        if not project:
            return analytic_ids

        for field_name in (
            "account_id",
            "analytic_account_id",
            "x_account_analytic_account_id",
        ):
            if field_name not in project._fields:
                continue

            analytic = project[field_name]

            if analytic:
                analytic_ids.update(analytic.ids)

        return analytic_ids

    def _get_sale_order_analytic_ids(self, order):
        analytic_ids = set()

        if not order:
            return analytic_ids

        for field_name in (
            "analytic_account_id",
            "x_account_analytic_account_id",
        ):
            if field_name not in order._fields:
                continue

            analytic = order[field_name]

            if analytic:
                analytic_ids.update(analytic.ids)

        project_analytic_ids = (
            self._get_project_analytic_ids(
                order.project_id
            )
        )

        for line in order.order_line:
            distribution = (
                line.analytic_distribution or {}
            )

            for distribution_key in distribution:
                line_analytic_ids = (
                    self._extract_analytic_ids(
                        distribution_key
                    )
                )

                analytic_ids.update(
                    line_analytic_ids
                    - project_analytic_ids
                )

        return analytic_ids

    def _get_analytic_ids_by_project(self, orders):
        result = {
            project_id: set()
            for project_id in orders.project_id.ids
        }

        for order in orders:
            project_id = order.project_id.id

            if not project_id:
                continue

            result.setdefault(
                project_id,
                set(),
            ).update(
                self._get_sale_order_analytic_ids(
                    order
                )
            )

        return result

    def _get_order_analytic_accounts(self, orders):
        analytic_ids = set()

        for order in orders:
            analytic_ids.update(
                self._get_sale_order_analytic_ids(
                    order
                )
            )

        return self.env[
            "account.analytic.account"
        ].browse(
            list(analytic_ids)
        ).exists()

    def _extract_analytic_ids(self, distribution_key):
        analytic_ids = set()

        for value in str(distribution_key).split(","):
            value = value.strip()

            if value.isdigit():
                analytic_ids.add(int(value))

        return analytic_ids

    def _get_bulk_journal_amounts(
        self,
        analytic_ids_by_project,
        date_from=False,
        date_to=False,
    ):
        empty_values = {
            "actual_expenses": 0.0,
            "actual_sales": 0.0,
            "retention": 0.0,
            "down_payment": 0.0,
            "lg": 0.0,
        }

        result = {
            int(project_id): dict(empty_values)
            for project_id in analytic_ids_by_project
        }

        analytic_project_rows = []

        for (
            project_id,
            analytic_ids,
        ) in analytic_ids_by_project.items():
            for analytic_id in analytic_ids:
                if analytic_id:
                    analytic_project_rows.append(
                        (
                            int(analytic_id),
                            int(project_id),
                        )
                    )

        if not analytic_project_rows:
            return result

        account_metric_rows = (
            self._get_account_metric_rows()
        )

        if not account_metric_rows:
            return result

        analytic_values_sql = ", ".join(
            ["(%s, %s)"] * len(analytic_project_rows)
        )

        account_values_sql = ", ".join(
            ["(%s, %s)"] * len(account_metric_rows)
        )

        company_ids = (
            self.env.companies.ids
            or [self.env.company.id]
        )

        date_conditions = ""
        date_params = []

        if date_from:
            date_conditions += """
                AND aml.date >= %s
            """
            date_params.append(date_from)

        if date_to:
            date_conditions += """
                AND aml.date <= %s
            """
            date_params.append(date_to)

        query = f"""
            WITH analytic_project_map (
                analytic_id,
                project_id
            ) AS (
                VALUES {analytic_values_sql}
            ),

            account_metric_map (
                account_id,
                metric
            ) AS (
                VALUES {account_values_sql}
            ),

            allocated_lines AS (
                SELECT
                    matched_project.project_id,
                    account_metric.metric,

                    (
                        aml.balance
                        *
                        LEAST(
                            GREATEST(
                                CASE
                                    WHEN
                                        distribution.percentage
                                        ~
                                        '^-?[0-9]+([.][0-9]+)?$'
                                    THEN
                                        distribution.percentage::numeric
                                    ELSE 0
                                END,
                                0
                            ),
                            100
                        )
                        / 100.0
                    ) AS allocated_balance

                FROM account_move_line aml

                JOIN account_metric_map account_metric
                    ON account_metric.account_id =
                       aml.account_id

                CROSS JOIN LATERAL jsonb_each_text(
                    COALESCE(
                        aml.analytic_distribution,
                        '{{}}'::jsonb
                    )
                ) AS distribution(
                    analytic_key,
                    percentage
                )

                JOIN LATERAL (
                    SELECT DISTINCT
                        analytic_map.project_id

                    FROM regexp_split_to_table(
                        distribution.analytic_key,
                        ','
                    ) AS analytic_part

                    JOIN analytic_project_map
                        analytic_map
                        ON
                            btrim(analytic_part)
                            ~ '^[0-9]+$'
                        AND
                            analytic_map.analytic_id =
                            btrim(
                                analytic_part
                            )::integer
                ) AS matched_project
                    ON TRUE

                WHERE aml.parent_state = 'posted'

                  AND aml.analytic_distribution
                      IS NOT NULL

                  AND aml.company_id = ANY(%s)

                  {date_conditions}
            )

            SELECT
                project_id,

                COALESCE(
                    SUM(
                        CASE
                            WHEN metric =
                                 'actual_expenses'
                            THEN allocated_balance
                            ELSE 0
                        END
                    ),
                    0
                ) AS actual_expenses,

                COALESCE(
                    SUM(
                        CASE
                            WHEN metric =
                                 'actual_sales'
                            THEN -allocated_balance
                            ELSE 0
                        END
                    ),
                    0
                ) AS actual_sales,

                COALESCE(
                    SUM(
                        CASE
                            WHEN metric = 'retention'
                            THEN allocated_balance
                            ELSE 0
                        END
                    ),
                    0
                ) AS retention,

                COALESCE(
                    SUM(
                        CASE
                            WHEN metric =
                                 'down_payment'
                            THEN allocated_balance
                            ELSE 0
                        END
                    ),
                    0
                ) AS down_payment,

                COALESCE(
                    SUM(
                        CASE
                            WHEN metric = 'lg'
                            THEN allocated_balance
                            ELSE 0
                        END
                    ),
                    0
                ) AS lg

            FROM allocated_lines

            GROUP BY project_id
        """

        params = []

        for analytic_id, project_id in (
            analytic_project_rows
        ):
            params.extend([
                analytic_id,
                project_id,
            ])

        for account_id, metric in (
            account_metric_rows
        ):
            params.extend([
                account_id,
                metric,
            ])

        params.append(company_ids)
        params.extend(date_params)

        self.env.cr.execute(query, params)

        for row in self.env.cr.dictfetchall():
            project_id = int(row["project_id"])

            result[project_id] = {
                "actual_expenses": float(
                    row["actual_expenses"] or 0.0
                ),
                "actual_sales": float(
                    row["actual_sales"] or 0.0
                ),
                "retention": float(
                    row["retention"] or 0.0
                ),
                "down_payment": float(
                    row["down_payment"] or 0.0
                ),
                "lg": float(
                    row["lg"] or 0.0
                ),
            }

        return result

    def _get_account_metric_rows(self):
        Account = self.env["account.account"]

        pnl_accounts = Account.search([
            (
                "account_type",
                "in",
                [
                    "income",
                    "income_other",
                    "expense",
                    "expense_depreciation",
                    "expense_direct_cost",
                ],
            ),
        ])

        sales_accounts = pnl_accounts.filtered(
            self._is_sales_account
        )

        expense_accounts = pnl_accounts.filtered(
            lambda account: (
                self._is_pnl_account(account)
                and not self._is_sales_account(account)
            )
        )

        retention_accounts = Account.search([
            ("code", "=", "12102"),
        ])

        down_payment_accounts = Account.search([
            ("code", "=", "12103"),
        ])

        lg_accounts = Account.search([
            ("code", "=", "1401"),
        ])

        account_metric = {}

        for account in expense_accounts:
            account_metric[
                account.id
            ] = "actual_expenses"

        for account in sales_accounts:
            account_metric[
                account.id
            ] = "actual_sales"

        for account in retention_accounts:
            account_metric[
                account.id
            ] = "retention"

        for account in down_payment_accounts:
            account_metric[
                account.id
            ] = "down_payment"

        for account in lg_accounts:
            account_metric[
                account.id
            ] = "lg"

        return [
            (
                account_id,
                metric,
            )
            for account_id, metric
            in account_metric.items()
        ]

    def _get_journal_item_ids_sql(
        self,
        analytic_ids,
        account_ids,
        date_from=False,
        date_to=False,
    ):
        analytic_ids = list({
            int(analytic_id)
            for analytic_id in analytic_ids
            if analytic_id
        })

        account_ids = list({
            int(account_id)
            for account_id in account_ids
            if account_id
        })

        if not analytic_ids or not account_ids:
            return []

        company_ids = (
            self.env.companies.ids
            or [self.env.company.id]
        )

        date_conditions = ""

        params = [
            account_ids,
            company_ids,
            analytic_ids,
        ]

        if date_from:
            date_conditions += """
                AND aml.date >= %s
            """
            params.append(date_from)

        if date_to:
            date_conditions += """
                AND aml.date <= %s
            """
            params.append(date_to)

        query = f"""
            SELECT DISTINCT
                aml.id

            FROM account_move_line aml

            CROSS JOIN LATERAL jsonb_object_keys(
                COALESCE(
                    aml.analytic_distribution,
                    '{{}}'::jsonb
                )
            ) AS distribution_key

            CROSS JOIN LATERAL regexp_split_to_table(
                distribution_key,
                ','
            ) AS analytic_part

            WHERE aml.parent_state = 'posted'

              AND aml.account_id = ANY(%s)

              AND aml.company_id = ANY(%s)

              AND aml.analytic_distribution
                  IS NOT NULL

              AND btrim(analytic_part)
                  ~ '^[0-9]+$'

              AND btrim(
                    analytic_part
                  )::integer = ANY(%s)

              {date_conditions}

            ORDER BY aml.id
        """

        self.env.cr.execute(query, params)

        return [
            row[0]
            for row in self.env.cr.fetchall()
        ]

    def _prepare_project_row_bulk(
        self,
        project,
        all_orders,
        period_orders,
        analytic_ids,
        journal_amounts,
    ):
        sales_orders_value = sum(
            all_orders.mapped("amount_untaxed")
        )

        adjusted_orders_value = (
            project.adjusted_orders_value or 0.0
        )

        total_sales_orders_value = (
            sales_orders_value
            + adjusted_orders_value
        )

        total_expected_expenses = sum(
            all_orders.mapped(
                "total_expected_expense"
            )
        )

        actual_expenses = journal_amounts.get(
            "actual_expenses",
            0.0,
        )

        actual_sales = journal_amounts.get(
            "actual_sales",
            0.0,
        )

        retention = journal_amounts.get(
            "retention",
            0.0,
        )

        down_payment = journal_amounts.get(
            "down_payment",
            0.0,
        )

        lg = journal_amounts.get(
            "lg",
            0.0,
        )

        poc = (
            actual_expenses
            / total_expected_expenses
            if total_expected_expenses
            else 0.0
        )

        if poc <= 1:
            ubr = (
                poc * total_sales_orders_value
            ) - actual_sales
        else:
            ubr = (
                total_sales_orders_value
                - actual_sales
            )

        is_done_project = (
            (project.stage_id.name or "")
            .strip()
            .lower()
            == "done"
        )

        if is_done_project:
            ubr = 0.0

        actual_revenue = actual_sales + ubr

        actual_gm = (
            (
                actual_revenue
                - actual_expenses
            )
            / actual_revenue
            if actual_revenue
            else 0.0
        )

        remaining_expected_expenses = (
            total_expected_expenses
            - actual_expenses
        )

        expected_sales = (
            total_sales_orders_value
            - actual_sales
            - ubr
        )

        if is_done_project:
            remaining_expected_expenses = 0.0
            expected_sales = 0.0

        expected_gm = (
            (
                expected_sales
                - remaining_expected_expenses
            )
            / expected_sales
            if expected_sales
            else 0.0
        )

        analytics = self.env[
            "account.analytic.account"
        ].browse(
            list(analytic_ids)
        ).exists().sorted(
            lambda analytic: analytic.name or ""
        )

        branch_field = self._get_branch_field()

        branches = (
            all_orders.mapped(branch_field)
            if branch_field
            else self.env["res.company"]
        )

        return {
            "project_id": project.id,
            "project": project.name or "",
            "status": project.stage_id.name or "",
            "sales_orders": ", ".join(
                all_orders.mapped("name")
            ),
            "analytic_accounts": [
                {
                    "id": analytic.id,
                    "name": analytic.name or "",
                }
                for analytic in analytics
            ],
            "branch": (
                ", ".join(
                    branches.mapped("name")
                )
                if branch_field
                else ""
            ),
            "partner": ", ".join(
                all_orders.partner_id.mapped("name")
            ),
            "sales_orders_value": sales_orders_value,
            "adjusted_orders_value": (
                adjusted_orders_value
            ),
            "total_sales_orders_value": (
                total_sales_orders_value
            ),
            "total_expected_expenses": (
                total_expected_expenses
            ),
            "actual_expenses": actual_expenses,
            "actual_sales": actual_sales,
            "poc": poc,
            "ubr": ubr,
            "retention": retention,
            "down_payment": down_payment,
            "lg": lg,
            "actual_gm": actual_gm,
            "remaining_expected_expenses": (
                remaining_expected_expenses
            ),
            "expected_sales": expected_sales,
            "expected_gm": expected_gm,
        }

    def _is_pnl_account(self, account):
        return account.account_type in {
            "income",
            "income_other",
            "expense",
            "expense_depreciation",
            "expense_direct_cost",
        }

    def _is_sales_account(self, account):
        if (
            "budget_group_id" in account._fields
            and account.budget_group_id
        ):
            budget_group = account.budget_group_id

            group_name = (
                budget_group.name or ""
            ).strip().lower()

            group_code = (
                getattr(
                    budget_group,
                    "code",
                    "",
                )
                or ""
            ).strip().lower()

            return (
                group_name == "sales"
                or group_code == "sales"
            )

        return account.account_type in {
            "income",
            "income_other",
        }

    def _get_metric_account_ids(self, metric):
        Account = self.env["account.account"]

        if metric == "retention":
            return Account.search([
                ("code", "=", "12102"),
            ]).ids

        if metric == "down_payment":
            return Account.search([
                ("code", "=", "12103"),
            ]).ids

        if metric == "lg":
            return Account.search([
                ("code", "=", "1401"),
            ]).ids

        accounts = Account.search([
            (
                "account_type",
                "in",
                [
                    "income",
                    "income_other",
                    "expense",
                    "expense_depreciation",
                    "expense_direct_cost",
                ],
            ),
        ])

        if metric == "actual_sales":
            return accounts.filtered(
                self._is_sales_account
            ).ids

        if metric == "actual_expenses":
            return accounts.filtered(
                lambda account: (
                    self._is_pnl_account(account)
                    and not self._is_sales_account(
                        account
                    )
                )
            ).ids

        return []

    def _metric_title(self, metric, project_name):
        titles = {
            "actual_expenses": _("Actual Expenses"),
            "actual_sales": _("Actual Sales"),
            "retention": _("Retention"),
            "down_payment": _("Advance Payment"),
            "lg": _("LG"),
        }

        return "%s - %s" % (
            titles.get(
                metric,
                _("Journal Items"),
            ),
            project_name,
        )

    def _prepare_totals(self, rows):
        amount_fields = [
            "sales_orders_value",
            "adjusted_orders_value",
            "total_sales_orders_value",
            "total_expected_expenses",
            "actual_expenses",
            "actual_sales",
            "ubr",
            "retention",
            "down_payment",
            "lg",
            "remaining_expected_expenses",
            "expected_sales",
        ]

        totals = {
            field_name: sum(
                row.get(field_name, 0.0)
                for row in rows
            )
            for field_name in amount_fields
        }

        totals["poc"] = (
            totals["actual_expenses"]
            / totals["total_expected_expenses"]
            if totals["total_expected_expenses"]
            else 0.0
        )

        actual_revenue = (
            totals["actual_sales"]
            + totals["ubr"]
        )

        totals["actual_gm"] = (
            (
                actual_revenue
                - totals["actual_expenses"]
            )
            / actual_revenue
            if actual_revenue
            else 0.0
        )

        totals["expected_gm"] = (
            (
                totals["expected_sales"]
                - totals[
                    "remaining_expected_expenses"
                ]
            )
            / totals["expected_sales"]
            if totals["expected_sales"]
            else 0.0
        )

        return totals

    def _write_excel_sheet(
        self,
        workbook,
        worksheet,
        data,
        filters,
    ):
        navy = "#16345B"
        blue = "#315F91"
        gold = "#C6A15B"
        white = "#FFFFFF"

        text_color = "#25282D"
        strong_text = "#111318"
        muted_text = "#5D636B"

        border_color = "#D9DEE5"
        even_row_color = "#FAFBFC"
        total_background = "#E9EFF6"

        title_format = workbook.add_format({
            "bold": True,
            "font_size": 18,
            "font_color": white,
            "bg_color": navy,
            "align": "center",
            "valign": "vcenter",
            "bottom": 3,
            "bottom_color": gold,
        })

        filter_format = workbook.add_format({
            "font_color": muted_text,
            "bg_color": white,
            "border": 1,
            "border_color": border_color,
            "align": "center",
            "valign": "vcenter",
        })

        header_format = workbook.add_format({
            "bold": True,
            "font_color": white,
            "bg_color": blue,
            "border": 1,
            "border_color": border_color,
            "bottom": 3,
            "bottom_color": gold,
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
        })

        center_text_format = workbook.add_format({
            "font_color": strong_text,
            "border": 1,
            "border_color": border_color,
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
        })

        center_text_even_format = workbook.add_format({
            "font_color": strong_text,
            "bg_color": even_row_color,
            "border": 1,
            "border_color": border_color,
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
        })

        left_text_format = workbook.add_format({
            "font_color": strong_text,
            "border": 1,
            "border_color": border_color,
            "align": "left",
            "valign": "vcenter",
            "text_wrap": True,
        })

        left_text_even_format = workbook.add_format({
            "font_color": strong_text,
            "bg_color": even_row_color,
            "border": 1,
            "border_color": border_color,
            "align": "left",
            "valign": "vcenter",
            "text_wrap": True,
        })

        amount_format = workbook.add_format({
            "font_color": text_color,
            "border": 1,
            "border_color": border_color,
            "align": "center",
            "valign": "vcenter",
            "num_format": "#,##0.00;[Red]-#,##0.00",
        })

        amount_even_format = workbook.add_format({
            "font_color": text_color,
            "bg_color": even_row_color,
            "border": 1,
            "border_color": border_color,
            "align": "center",
            "valign": "vcenter",
            "num_format": "#,##0.00;[Red]-#,##0.00",
        })

        percentage_format = workbook.add_format({
            "font_color": text_color,
            "border": 1,
            "border_color": border_color,
            "align": "center",
            "valign": "vcenter",
            "num_format": "0.00%",
        })

        percentage_even_format = workbook.add_format({
            "font_color": text_color,
            "bg_color": even_row_color,
            "border": 1,
            "border_color": border_color,
            "align": "center",
            "valign": "vcenter",
            "num_format": "0.00%",
        })

        total_text_format = workbook.add_format({
            "bold": True,
            "font_color": strong_text,
            "bg_color": total_background,
            "border": 1,
            "border_color": border_color,
            "top": 2,
            "top_color": blue,
            "align": "center",
            "valign": "vcenter",
        })

        total_amount_format = workbook.add_format({
            "bold": True,
            "font_color": strong_text,
            "bg_color": total_background,
            "border": 1,
            "border_color": border_color,
            "top": 2,
            "top_color": blue,
            "align": "center",
            "valign": "vcenter",
            "num_format": "#,##0.00;[Red]-#,##0.00",
        })

        total_percentage_format = workbook.add_format({
            "bold": True,
            "font_color": strong_text,
            "bg_color": total_background,
            "border": 1,
            "border_color": border_color,
            "top": 2,
            "top_color": blue,
            "align": "center",
            "valign": "vcenter",
            "num_format": "0.00%",
        })

        headers = [
            ("project", _("Project"), "text"),
            ("status", _("Status"), "text"),
            ("sales_orders", _("Sales Orders"), "text"),
            (
                "analytic_accounts",
                _("Analytic Accounts"),
                "text",
            ),
            ("branch", _("Branch"), "text"),
            ("partner", _("Partner"), "text"),
            (
                "sales_orders_value",
                _("Sales Orders Value"),
                "amount",
            ),
            (
                "adjusted_orders_value",
                _("Adjusted Orders Value"),
                "amount",
            ),
            (
                "total_sales_orders_value",
                _("Total Sales Orders Value"),
                "amount",
            ),
            (
                "total_expected_expenses",
                _("Total Expected Expenses"),
                "amount",
            ),
            (
                "actual_expenses",
                _("Actual Expenses"),
                "amount",
            ),
            (
                "actual_sales",
                _("Actual Sales"),
                "amount",
            ),
            ("poc", _("POC %"), "percentage"),
            ("ubr", _("UBR"), "amount"),
            (
                "retention",
                _("Retention (12102)"),
                "amount",
            ),
            (
                "down_payment",
                _("Advance Payment (12103)"),
                "amount",
            ),
            (
                "lg",
                _("LG (1401)"),
                "amount",
            ),
            (
                "actual_gm",
                _("Actual GM %"),
                "percentage",
            ),
            (
                "remaining_expected_expenses",
                _("Expected Expenses"),
                "amount",
            ),
            (
                "expected_sales",
                _("Expected Sales"),
                "amount",
            ),
            (
                "expected_gm",
                _("Expected GM %"),
                "percentage",
            ),
        ]

        worksheet.hide_gridlines(2)
        worksheet.set_tab_color(blue)

        worksheet.merge_range(
            0,
            0,
            0,
            len(headers) - 1,
            "Project Status & UBR",
            title_format,
        )

        worksheet.set_row(0, 32)

        period_text = "%s: %s    %s: %s" % (
            _("Date From"),
            filters.get("date_from") or _("All"),
            _("Date To"),
            filters.get("date_to") or _("All"),
        )

        worksheet.merge_range(
            1,
            0,
            1,
            len(headers) - 1,
            period_text,
            filter_format,
        )

        worksheet.set_row(1, 22)

        header_row = 3

        for column, (
            _key,
            label,
            _value_type,
        ) in enumerate(headers):
            worksheet.write(
                header_row,
                column,
                label,
                header_format,
            )

        worksheet.set_row(header_row, 42)

        multiline_fields = {
            "sales_orders",
            "analytic_accounts",
            "branch",
            "partner",
        }

        left_aligned_fields = {
            "analytic_accounts",
            "partner",
        }

        def _split_values(value):
            if not value:
                return []

            if isinstance(value, (list, tuple)):
                values = []

                for item in value:
                    if isinstance(item, dict):
                        item_value = item.get("name", "")
                    else:
                        item_value = str(item or "")

                    item_value = item_value.strip()

                    if item_value:
                        values.append(item_value)

                return values

            return [
                item.strip()
                for item in str(value).split(",")
                if item.strip()
            ]

        def _format_multiline(value):
            return "\n".join(
                "* %s" % item
                for item in _split_values(value)
            )

        column_widths = {
            "project": 25,
            "status": 15,
            "sales_orders": 19,
            "analytic_accounts": 29,
            "branch": 17,
            "partner": 31,
        }

        def _estimate_wrapped_lines(value, width):
            text_value = str(value or "")

            if not text_value:
                return 1

            total_lines = 0

            for explicit_line in text_value.split("\n"):
                line_length = len(explicit_line)

                total_lines += max(
                    1,
                    (
                        line_length
                        + width
                        - 1
                    )
                    // width,
                )

            return max(total_lines, 1)

        first_data_row = header_row + 1

        for row_index, row in enumerate(
            data["rows"],
            start=first_data_row,
        ):
            is_even = (
                (
                    row_index
                    - first_data_row
                )
                % 2
                == 1
            )

            maximum_lines = 1

            for key, _label, value_type in headers:
                if value_type != "text":
                    continue

                value = row.get(key, "")

                display_value = (
                    _format_multiline(value)
                    if key in multiline_fields
                    else value or ""
                )

                estimated_lines = _estimate_wrapped_lines(
                    display_value,
                    column_widths.get(key, 20),
                )

                maximum_lines = max(
                    maximum_lines,
                    estimated_lines,
                )

            row_height = min(
                409,
                max(
                    24,
                    (
                        maximum_lines * 15
                    )
                    + 6,
                ),
            )

            worksheet.set_row(
                row_index,
                row_height,
            )

            for column, (
                key,
                _label,
                value_type,
            ) in enumerate(headers):
                value = row.get(key, "")

                if value_type == "amount":
                    worksheet.write_number(
                        row_index,
                        column,
                        float(value or 0.0),
                        (
                            amount_even_format
                            if is_even
                            else amount_format
                        ),
                    )

                elif value_type == "percentage":
                    worksheet.write_number(
                        row_index,
                        column,
                        float(value or 0.0),
                        (
                            percentage_even_format
                            if is_even
                            else percentage_format
                        ),
                    )

                else:
                    display_value = (
                        _format_multiline(value)
                        if key in multiline_fields
                        else value or ""
                    )

                    if key in left_aligned_fields:
                        cell_format = (
                            left_text_even_format
                            if is_even
                            else left_text_format
                        )
                    else:
                        cell_format = (
                            center_text_even_format
                            if is_even
                            else center_text_format
                        )

                    worksheet.write(
                        row_index,
                        column,
                        display_value,
                        cell_format,
                    )

        total_row = (
            first_data_row
            + len(data["rows"])
        )

        worksheet.merge_range(
            total_row,
            0,
            total_row,
            5,
            _("Total"),
            total_text_format,
        )

        for column, (
            key,
            _label,
            value_type,
        ) in enumerate(
            headers[6:],
            start=6,
        ):
            value = data["totals"].get(
                key,
                0.0,
            )

            worksheet.write_number(
                total_row,
                column,
                float(value or 0.0),
                (
                    total_percentage_format
                    if value_type == "percentage"
                    else total_amount_format
                ),
            )

        worksheet.set_row(total_row, 25)

        worksheet.freeze_panes(
            header_row + 1,
            1,
        )

        if data["rows"]:
            worksheet.autofilter(
                header_row,
                0,
                total_row - 1,
                len(headers) - 1,
            )
        else:
            worksheet.autofilter(
                header_row,
                0,
                header_row,
                len(headers) - 1,
            )

        worksheet.set_column(0, 0, 25)
        worksheet.set_column(1, 1, 15)
        worksheet.set_column(2, 2, 22)
        worksheet.set_column(3, 3, 29)
        worksheet.set_column(4, 4, 17)
        worksheet.set_column(5, 5, 31)

        worksheet.set_column(
            6,
            len(headers) - 1,
            20,
        )

        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.fit_to_pages(1, 0)

        worksheet.set_margins(
            0.25,
            0.25,
            0.5,
            0.5,
        )

        worksheet.repeat_rows(
            header_row,
            header_row,
        )