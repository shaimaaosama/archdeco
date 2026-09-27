from odoo import fields, models, api


class ProjectProject(models.Model):
    _inherit = "project.project"

    adjusted_orders_value = fields.Monetary(
        string="Adjusted Orders Value",
        currency_field="company_currency_id",
        tracking=True,
    )
    expected_expenses = fields.Monetary(
        string="Expected Expenses",
        currency_field="company_currency_id",
        tracking=True,
    )
    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        defaults = self.default_get([
            "allow_timesheets",
            "account_id",
        ])

        for vals in vals_list:
            account_id = vals.get(
                "account_id",
                defaults.get("account_id"),
            )

            if not account_id:
                vals["allow_timesheets"] = False
                vals["account_id"] = False

        return super().create(vals_list)

    def write(self, vals):
        if (
            vals.get("allow_timesheets")
            and not vals.get("account_id")
        ):
            projects_without_account = self.filtered(
                lambda project: not project.account_id
            )

            if projects_without_account:
                raise ValidationError(
                    _(
                        "You cannot enable Timesheets without "
                        "selecting an analytic account manually."
                    )
                )

        return super().write(vals)

    def _create_analytic_account(self):
        return self.env["account.analytic.account"]