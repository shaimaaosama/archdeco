# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, fields, models
from odoo.osv import expression

class ShResUsers(models.Model):
    _inherit = 'res.users'

    journal_ids = fields.Many2many(
        'account.journal', string="Journals", copy=False)

class ShAccountJournalRestrict(models.Model):
    _inherit = 'account.journal'

    user_ids = fields.Many2many(
        'res.users', string="Users", copy=False)

    # To apply domain to action_________ 2
    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     super(ShAccountJournalRestrict, self)._name_search(
    #         name, args=None, operator='ilike', limit=100, name_get_uid=None)
    #
    #     if(
    #         self.env.user.has_group("sh_journal_restrict.group_journal_restrict_feature") and not
    #         (self.env.user.has_group("base.group_erp_manager"))
    #     ):
    #         domain = [
    #             ("user_ids", "in", self.env.user.id),
    #         ]
    #     else:
    #         domain = []
    #     return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
    #
    # # To apply domain to load menu_________ 1
    @api.model
    def _search(self, args, offset=0, limit=None, order=None):
        _ = self._context or {}
        if(
            self.env.user.has_group("sh_journal_restrict.group_journal_restrict_feature")

        ):
            args += [
                ("id", "in", self.env.user.journal_ids.ids),
            ]
        return super(ShAccountJournalRestrict, self)._search(
            args,
            offset=offset,
            limit=limit,
            order=order,

        )
    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
    #     args = args or []
    #
    #     # Get the current user
    #
    #     user = self.env.user
    #
    #     # Restrict to analytic accounts the user owns
    #     allowed_ids = user.journal_ids.ids
    #
    #     # Only keep search results in those IDs
    #     if allowed_ids:
    #         args += [('id', 'in', allowed_ids)]
    #     else:
    #         # If the user has none, return empty
    #         return []
    #
    #     # If name contains something, Odoo will automatically handle the matching
    #     # on rec_name (usually name field) + our args.
    #     return super(ShAccountJournalRestrict, self).name_search(
    #         name=name,
    #         args=args,
    #         operator=operator,
    #         limit=limit,
    #     )

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.depends('company_id', 'partner_id')
    def _compute_journal_id(self):
        # for payment in self:
        #     # default customer payment method logic
        #     partner = payment.partner_id
        #     payment_type = payment.payment_type if payment.payment_type in ('inbound', 'outbound') else None
        #     if not bool(payment._origin) and (partner or payment_type):
        #         field_name = f'property_{payment_type}_payment_method_line_id'
        #         default_payment_method_line = payment.partner_id.with_company(payment.company_id)[field_name]
        #         journal = default_payment_method_line.journal_id
        #         if journal:
        #             payment.journal_id = journal
        #             continue
        #
        #     company = payment.company_id or self.env.company
        #     if not payment.journal_id or company != payment.journal_id.company_id:
        #         payment.journal_id = self.env['account.journal'].search([
        #             *self.env['account.journal']._check_company_domain(company),
        #             ('type', 'in', ['bank', 'cash', 'credit']),('id', 'in', self.env.user.journal_ids.ids)
        #         ], limit=1)
        pass
