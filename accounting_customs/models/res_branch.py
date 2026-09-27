from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class ResBranchInherit(models.Model):
    _inherit = 'res.branch'

    cinema_product_tag_ids = fields.Many2many(
        comodel_name='product.tag',
        string='Cinema Product Tags',
    )

    is_cinema_branch = fields.Boolean(
        string='Is Cinema Branch',
    )