from odoo import api, fields, models, Command, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

#
# class PyamentInherit(models.Model):
#     _inherit = 'account.payment'
#
#     @api.model
#     def _get_default_journal(self):
#         journal = None
#
#         return journal

class AccountInherit(models.Model):
    _inherit = 'account.move'

    # @api.model
    # def _get_default_journal(self):
    #     journal = None
    #     return journal

    @api.model
    def _get_default_currency(self):
        move_type = self._context.get('default_move_type', 'entry')
        if move_type in self.get_sale_types(include_receipts=True):
            journal_types = ['sale']
        elif move_type in self.get_purchase_types(include_receipts=True):
            journal_types = ['purchase']
        else:
            journal_types = self._context.get('default_move_journal_types', ['general'])

        if self._context.get('default_journal_id'):
            journal = self.env['account.journal'].browse(self._context['default_journal_id'])

            if move_type != 'entry' and journal.type not in journal_types:
                raise UserError(_(
                    "Cannot create an invoice of type %(move_type)s with a journal having %(journal_type)s as type.",
                    move_type=move_type,
                    journal_type=journal.type,
                ))
        else:
            journal = self._search_default_journal()

        return journal.currency_id or journal.company_id.currency_id

    # journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
    #     states={'draft': [('readonly', False)]},
    #     check_company=True, domain="[('id', 'in', suitable_journal_ids)]",
    #     default=_get_default_journal)

    # currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True,
    #     states={'draft': [('readonly', False)]},
    #     string='Currency',
    #     default=_get_default_currency)