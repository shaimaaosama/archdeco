import json
from odoo import models, fields, api

class AnalyticDomainMixin(models.AbstractModel):
    _name = "analytic.domain.mixin"
    _description = "Mixin to compute domain based on user analytic accounts"

    analytic_domain = fields.Char(
        compute="_compute_analytic_domain",
        readonly=True,
        store=False,
    )

    @api.depends('partner_id')
    def _compute_analytic_domain(self):
        allowed = self.env.user.account_analytic_account_ids.ids or []
        for rec in self:
            # make sure always a valid domain array
            if allowed:
                rec.analytic_domain = json.dumps([('id', 'in', allowed)])
            else:
                # this domain results in no records if user has none
                rec.analytic_domain = json.dumps([('id', '=', False)])
