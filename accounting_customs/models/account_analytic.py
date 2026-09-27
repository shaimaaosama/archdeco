from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class AccountAnalyticInherit(models.Model):
    _inherit = 'account.analytic.account'

    branch_distribution_line_ids = fields.One2many(
        "analytic.account.branch.line",
        "analytic_account_id",
        string="Branch Distribution",
    )
    branch_distribution = fields.Char(compute="_compute_branch_distribution",
        store=True,)

    @api.constrains("branch_distribution_line_ids", "branch_distribution_line_ids.percentage")
    def _check_branch_distribution_total(self):
        for rec in self:
            if not rec.branch_distribution_line_ids:
                raise ValidationError(_("Please set branch distribution."))
            total = sum(rec.branch_distribution_line_ids.mapped("percentage"))
            if total != 100:
                raise ValidationError(_("Branch distribution total must be 100%% (now it's: %s%%).") % total)

    @api.depends('branch_distribution_line_ids','branch_distribution_line_ids.branch_id','branch_distribution_line_ids.branch_id.name',)
    def _compute_branch_distribution(self):
        for rec in self:
            branch_names = rec.branch_distribution_line_ids.mapped('branch_id.name')
            branch_names = [name for name in set(branch_names) if name]

            if not branch_names:
                rec.branch_distribution = "No Branch"
            elif len(branch_names) == 1:
                rec.branch_distribution = branch_names[0]
            else:
                rec.branch_distribution = "Shared"

class AnalyticAccountBranchLine(models.Model):
    _name = "analytic.account.branch.line"
    _description = "Analytic Account Branch Distribution"

    branch_id = fields.Many2one("res.branch", required=True)
    percentage = fields.Float(required=True, default=100.0)
    analytic_account_id = fields.Many2one( "account.analytic.account", ondelete="cascade")

    _sql_constraints = [
        ("uniq_branch_per_aa", "unique(analytic_account_id, branch_id)", "Branch already added."),
    ]

class AnalyticTag(models.Model):
    _name = 'analytic.tag'

    name = fields.Char(required=True)

    _sql_constraints = [
        ("uniq_name_analytic_tag", "unique(name)", "Tag already added."),
    ]