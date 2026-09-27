from odoo import models, fields

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_penalties_journal = fields.Boolean(
        string="Is Penalties",
        help="If checked, this journal will be used for Penalties & Awards entries."
    )
