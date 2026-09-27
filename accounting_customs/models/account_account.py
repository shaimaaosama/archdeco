from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountAccountInherit(models.Model):
    _inherit = "account.account"

    budget_group_id = fields.Many2one(comodel_name="budget.group", tracking=True,)

    @api.constrains("account_type", "budget_group_id")
    def _check_budget_group_required_for_pandl(self):
        if (
            self.env.context.get("install_mode")
            or self.env.context.get("module")
            or self.env.context.get("chart_template_loading")
            or self.env.context.get("skip_budget_group_validation")
        ):
            return

        pandl_types = (
            "income",
            "income_other",
            "expense",
            "expense_direct_cost",
            "expense_depreciation",
        )

        accounts_without_budget_group = self.filtered(
            lambda account: account.account_type in pandl_types
            and not account.budget_group_id
        )

        if accounts_without_budget_group:
            account_names = "\n".join(
                "- %s" % account.display_name
                for account in accounts_without_budget_group
            )

            raise ValidationError(
                _(
                    "Budget Group is required for P&L accounts.\n\n%s"
                )
                % account_names
            )