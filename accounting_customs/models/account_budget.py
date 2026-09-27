from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import ValidationError


class AccountReportBudgetInherit(models.Model):
    _name = 'account.report.budget'
    _inherit = ['account.report.budget', 'mail.thread', 'mail.activity.mixin']

    def _default_start_date(self):
        today = date.today()
        return date(today.year, 1, 1)

    def _default_end_date(self):
        today = date.today()
        return date(today.year, 12, 31)

    name = fields.Char(
        compute="_compute_budget_name",
        store=True,
    )

    start_date = fields.Date(
        required=True,
        default=_default_start_date,
        tracking=True,
    )

    end_date = fields.Date(
        required=True,
        default=_default_end_date,
        tracking=True,
    )

    budget_year = fields.Integer(
        string="Budget Year",
        compute="_compute_budget_year",
        store=True,
        index=True,
    )

    branch_id = fields.Many2one(
        "res.branch",
        required=True,
        tracking=True,
    )

    included_branch_ids = fields.Many2many(
        "res.branch",
        tracking=True,
        string="Included Branches",
    )

    type = fields.Selection(
        [
            ('group', 'By Budget Group'),
            ('account', 'By Account'),
        ],
        default='group',
        tracking=True,
    )

    budget_line_ids = fields.One2many(
        "account.budget.line",
        "budget_id",
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
        ],
        default='draft',
        tracking=True,
    )

    total_planned_amount = fields.Float(
        string="Planned",
        compute="_compute_budget_totals",
        store=True,
    )

    total_theoretical_amount = fields.Float(
        string="Theoretical",
        compute="_compute_budget_totals",
        store=True,
    )

    total_actual_amount = fields.Float(
        string="Actual",
        compute="_compute_budget_totals",
        store=True,
    )

    total_difference_amount = fields.Float(
        string="Difference",
        compute="_compute_budget_totals",
        store=True,
    )

    is_over_target = fields.Boolean(
        string="Over Target",
        compute="_compute_budget_totals",
        store=True,
    )

    is_over_budget = fields.Boolean(
        string="Over Budget",
        compute="_compute_budget_totals",
        store=True,
    )

    allowed_user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='account_report_budget_allowed_user_rel',
        column1='budget_id',
        column2='user_id',
        string='Allowed Users',
        tracking=True,
        domain=[('active', '=', True)],
        help='Users allowed to access this budget and its dashboard information.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        budgets = super().create(vals_list)

        for budget in budgets:
            if budget.type == 'group' and not budget.budget_line_ids:
                lines_vals = []

                for group in self.env['budget.group'].search([]):
                    lines_vals.append((0, 0, {
                        'budget_group_id': group.id,
                        'planned_amount': 0.0,
                    }))

                budget.write({
                    'budget_line_ids': lines_vals,
                })

        return budgets

    @api.constrains('start_date', 'end_date')
    def _check_budget_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.start_date > rec.end_date:
                raise ValidationError(_(
                    "Budget start date cannot be greater than end date."
                ))

    @api.depends('start_date')
    def _compute_budget_year(self):
        for rec in self:
            rec.budget_year = rec.start_date.year if rec.start_date else False

    @api.depends('start_date', 'end_date', 'branch_id')
    def _compute_budget_name(self):
        for rec in self:
            if not rec.start_date or not rec.end_date or not rec.branch_id:
                rec.name = False
                continue

            start = rec.start_date
            end = rec.end_date
            branch_name = rec.branch_id.name
            year = start.year

            if (
                start.month == 1
                and start.day == 1
                and end.month == 12
                and end.day == 31
                and start.year == end.year
            ):
                period = str(year)

            elif start.year == end.year and start.month == end.month:
                period = start.strftime('%b %Y')

            elif start.year == end.year and start.day == 1:
                quarter_map = {
                    (1, 3): 'Q1',
                    (4, 6): 'Q2',
                    (7, 9): 'Q3',
                    (10, 12): 'Q4',
                }

                period = False

                for (q_start, q_end), q_name in quarter_map.items():
                    if start.month == q_start and end.month == q_end:
                        period = f"{q_name} {year}"
                        break

                if not period:
                    period = f"{start.strftime('%b')} - {end.strftime('%b %Y')}"

            elif start.year == end.year and start.day == 1:
                if start.month == 1 and end.month == 6:
                    period = f"H1 {year}"
                elif start.month == 7 and end.month == 12:
                    period = f"H2 {year}"
                else:
                    period = f"{start.strftime('%b')} - {end.strftime('%b %Y')}"

            else:
                period = f"{start.strftime('%d-%m-%Y')} - {end.strftime('%d-%m-%Y')}"

            rec.name = f"Budget for {branch_name} - {period}"

    def action_submit(self):
        approve_group = self.env.ref(
            'accounting_customs.group_budget_approve',
            raise_if_not_found=False,
        )
        activity_type = self.env.ref(
            'mail.mail_activity_data_todo',
            raise_if_not_found=False,
        )

        for budget in self:
            if not sum(budget.budget_line_ids.mapped('planned_amount')):
                raise ValidationError(_(
                    "You cannot submit a budget with zero total amount."
                ))

            if approve_group and activity_type:
                for user in approve_group.users:
                    budget.activity_schedule(
                        activity_type_id=activity_type.id,
                        user_id=user.id,
                        summary=_("Budget Approval"),
                        note=_("%s") % budget.display_name,
                    )

            budget.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reset_to_draft(self):
        activity_type = self.env.ref(
            'mail.mail_activity_data_todo',
            raise_if_not_found=False,
        )

        for budget in self:
            domain = [
                ('res_model', '=', budget._name),
                ('res_id', '=', budget.id),
            ]

            if activity_type:
                domain.append(('activity_type_id', '=', activity_type.id))

            activities = self.env['mail.activity'].sudo().search(domain)

            activities = activities.filtered(
                lambda a:
                a.summary == 'Budget Approval'
                or 'approval' in (a.summary or '').lower()
            )

            activities.unlink()
            budget.write({'state': 'draft'})

    def unlink(self):
        for budget in self:
            if budget.state != 'draft':
                raise ValidationError(_(
                    "You can delete only Draft budgets."
                ))

        return super().unlink()

    @api.depends(
        "budget_line_ids.planned_amount",
        "budget_line_ids.theoretical_planned_amount",
        "budget_line_ids.actual_amount",
        "budget_line_ids.difference_amount",
        "budget_line_ids.budget_group_id",
    )
    def _compute_budget_totals(self):
        Account = self.env['account.account']

        all_group_ids = self.mapped('budget_line_ids.budget_group_id').ids

        accounts = Account.search([
            ('budget_group_id', 'in', all_group_ids),
        ])

        group_account_types = {}

        for acc in accounts:
            if not acc.budget_group_id:
                continue

            group_account_types.setdefault(
                acc.budget_group_id.id,
                set()
            ).add(acc.account_type)

        for budget in self:
            total_planned = 0.0
            total_theoretical = 0.0
            total_actual = 0.0
            total_difference = 0.0

            total_target_variance = 0.0
            total_budget_variance = 0.0

            for line in budget.budget_line_ids:
                planned = line.planned_amount or 0.0
                theoretical = line.theoretical_planned_amount or 0.0
                actual = line.actual_amount or 0.0
                difference = line.difference_amount or 0.0

                total_planned += planned
                total_theoretical += theoretical
                total_actual += actual
                total_difference += difference

                if not line.budget_group_id:
                    continue

                account_types = group_account_types.get(
                    line.budget_group_id.id,
                    set()
                )

                if any(t in ('income', 'income_other') for t in account_types):
                    if difference < 0:
                        total_target_variance += abs(difference)
                    elif difference > 0:
                        total_budget_variance += abs(difference)

                if any(t in (
                    'expense',
                    'expense_direct_cost',
                    'expense_depreciation',
                ) for t in account_types):
                    if difference < 0:
                        total_target_variance += abs(difference)
                    elif difference > 0:
                        total_budget_variance += abs(difference)

            budget.total_planned_amount = total_planned
            budget.total_theoretical_amount = total_theoretical
            budget.total_actual_amount = total_actual
            budget.total_difference_amount = total_difference

            budget.is_over_target = (
                total_target_variance > total_budget_variance
            )

            budget.is_over_budget = (
                total_budget_variance > total_target_variance
            )

    def action_recompute_budget_amounts(self):
        lines = self.mapped('budget_line_ids')

        lines._compute_theoretical_planned_amount()
        lines._compute_actual_amount()
        lines._compute_difference_amount()

        self._compute_budget_totals()

        return True


class AccountBudgetLine(models.Model):
    _name = 'account.budget.line'
    _description = 'Account Budget Line'
    _order = 'sequence asc, id asc'

    budget_id = fields.Many2one(
        'account.report.budget',
        ondelete='cascade',
    )

    sequence = fields.Integer()

    budget_group_id = fields.Many2one(
        'budget.group',
        required=True,
    )

    planned_amount = fields.Float(
        string="Planned",
    )

    theoretical_planned_amount = fields.Float(
        string="Theoretical",
        compute="_compute_theoretical_planned_amount",
        store=True,
    )

    actual_amount = fields.Float(
        string="Actual",
        compute='_compute_actual_amount',
        store=True,
    )

    difference_amount = fields.Float(
        string="Difference",
        compute='_compute_difference_amount',
        store=True,
    )

    is_over_target = fields.Boolean(
        compute="_compute_budget_colors",
        store=True,
    )

    is_over_budget = fields.Boolean(
        compute="_compute_budget_colors",
        store=True,
    )

    @api.constrains('budget_id', 'budget_group_id')
    def _check_unique_budget_group_line(self):
        for line in self:
            if not line.budget_id or not line.budget_group_id:
                continue

            duplicate = self.search_count([
                ('id', '!=', line.id),
                ('budget_id', '=', line.budget_id.id),
                ('budget_group_id', '=', line.budget_group_id.id),
            ])

            if duplicate:
                raise ValidationError(_(
                    "Budget group already added to this budget."
                ))

    @api.depends('difference_amount', 'budget_group_id')
    def _compute_budget_colors(self):
        Account = self.env['account.account']

        group_ids = self.mapped('budget_group_id').ids

        accounts = Account.search([
            ('budget_group_id', 'in', group_ids),
        ])

        group_account_types = {}

        for acc in accounts:
            if not acc.budget_group_id:
                continue

            group_account_types.setdefault(
                acc.budget_group_id.id,
                set()
            ).add(acc.account_type)

        for line in self:
            line.is_over_target = False
            line.is_over_budget = False

            if not line.budget_group_id:
                continue

            account_types = group_account_types.get(
                line.budget_group_id.id,
                set()
            )

            if any(t in ('income', 'income_other') for t in account_types):
                if line.difference_amount < 0:
                    line.is_over_target = True

            if any(t in (
                'expense',
                'expense_direct_cost',
                'expense_depreciation',
            ) for t in account_types):
                if line.difference_amount > 0:
                    line.is_over_budget = True

    @api.depends(
        'budget_group_id',
        'budget_id.branch_id',
        'budget_id.included_branch_ids',
        'budget_id.start_date',
        'budget_id.end_date',
    )
    def _compute_actual_amount(self):
        for line in self:
            line.actual_amount = 0.0

        valid_lines = self.filtered(lambda l:
            l.budget_group_id
            and l.budget_id
            and l.budget_id.branch_id
            and l.budget_id.start_date
            and l.budget_id.end_date
        )

        if not valid_lines:
            return

        AccountMoveLine = self.env['account.move.line']

        for budget in valid_lines.mapped('budget_id'):
            budget_lines = valid_lines.filtered(
                lambda l: l.budget_id == budget
            )

            budget_group_ids = budget_lines.mapped('budget_group_id').ids

            branch_ids = list(set(
                budget.branch_id.ids + budget.included_branch_ids.ids
            ))

            domain = [
                ('account_id.budget_group_id', 'in', budget_group_ids),
                ('branch_id', 'in', branch_ids),
                ('date', '>=', budget.start_date),
                ('date', '<=', budget.end_date),
                ('move_id.state', '=', 'posted'),
                ('display_type', 'not in', ('line_section', 'line_note')),
            ]

            grouped_data = AccountMoveLine.read_group(
                domain=domain,
                fields=['balance:sum', 'account_id'],
                groupby=['account_id'],
                lazy=False,
            )

            totals_by_budget_group = {}

            account_ids = [
                data['account_id'][0]
                for data in grouped_data
                if data.get('account_id')
            ]

            accounts = self.env['account.account'].browse(account_ids)
            accounts_by_id = {
                account.id: account
                for account in accounts
            }

            for data in grouped_data:
                account_data = data.get('account_id')

                if not account_data:
                    continue

                account = accounts_by_id.get(account_data[0])

                if not account or not account.budget_group_id:
                    continue

                amount = data.get('balance', 0.0) or 0.0

                if account.account_type in (
                    'income',
                    'income_other',
                    'expense',
                    'expense_direct_cost',
                    'expense_depreciation',
                ):
                    amount = -amount

                totals_by_budget_group[account.budget_group_id.id] = (
                    totals_by_budget_group.get(
                        account.budget_group_id.id,
                        0.0
                    ) + amount
                )

            for line in budget_lines:
                line.actual_amount = totals_by_budget_group.get(
                    line.budget_group_id.id,
                    0.0
                )

    @api.depends(
        'planned_amount',
        'budget_id.start_date',
        'budget_id.end_date',
    )
    def _compute_theoretical_planned_amount(self):
        today = fields.Date.context_today(self)

        for line in self:
            line.theoretical_planned_amount = 0.0

            if (
                not line.planned_amount
                or not line.budget_id
                or not line.budget_id.start_date
                or not line.budget_id.end_date
            ):
                continue

            start_date = line.budget_id.start_date
            end_date = line.budget_id.end_date

            if end_date < start_date:
                continue

            total_days = (end_date - start_date).days + 1

            if today <= start_date:
                elapsed_days = 0
            elif today >= end_date:
                elapsed_days = total_days
            else:
                elapsed_days = (today - start_date).days + 1

            line.theoretical_planned_amount = (
                line.planned_amount / total_days
            ) * elapsed_days

    @api.depends(
        'theoretical_planned_amount',
        'actual_amount',
    )
    def _compute_difference_amount(self):
        for line in self:
            line.difference_amount = (
                line.theoretical_planned_amount - line.actual_amount
            )


class BudgetGroup(models.Model):
    _name = 'budget.group'
    _description = 'Budget Group'
    _order = 'sequence asc, id asc'

    name = fields.Char(required=True)
    sequence = fields.Integer()

    _sql_constraints = [
        (
            "uniq_name_budget_group",
            "unique(name)",
            "Budget group already added.",
        ),
    ]