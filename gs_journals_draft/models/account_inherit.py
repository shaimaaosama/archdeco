# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class AccountJournalInherit(models.AbstractModel):
    _inherit = 'account.journal'

    is_draft = fields.Boolean(string='Is Draft ?')
    users_post_ids = fields.Many2many('res.users', 'users_post_ids11','users_post_ids22','users_post_ids33', string="Users Post")
    users_reset_draft_ids = fields.Many2many('res.users', 'users_post_ids111','users_post_ids222','users_post_ids333', string="Users Reset To Draft ")
    users_cancel_ids = fields.Many2many('res.users', 'users_post_ids1111','users_post_ids2222','users_post_ids3333', string="Users Cancel")


class AccountMoveInherit(models.AbstractModel):
    _inherit = 'account.move'

    is_draft = fields.Boolean(string='Is Draft ?', related='journal_id.is_draft')
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('gs_posted', 'Approved'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')

    def action_post(self):
        for rec in self:
            current_user = rec.env.user.id
            if current_user not in rec.journal_id.users_post_ids.ids:
                raise ValidationError(_("You don't have permission to post."))
        result = super(AccountMoveInherit, self).action_post()
        return result

    def button_draft(self):
        for rec in self:
            current_user = rec.env.user.id
            if current_user not in rec.journal_id.users_reset_draft_ids.ids:
                raise ValidationError(_("You don't have permission to reset to draft."))
        result = super(AccountMoveInherit, self).button_draft()
        return result

    def button_cancel(self):
        for rec in self:
            current_user = rec.env.user.id
            if current_user not in rec.journal_id.users_cancel_ids.ids:
                raise ValidationError(_("You don't have permission to cancel."))
        result = super(AccountMoveInherit, self).button_cancel()
        return result


class AccountPaymentInherit(models.AbstractModel):
    _inherit = 'account.payment'

    is_draft = fields.Boolean(string='Is Draft ?', related='journal_id.is_draft')

    def action_confirm_post(self):
        for rec in self:
            rec.state = 'gs_posted'

    def action_gs_post(self):
        for rec in self:
            journal_entry = self.env['account.move'].search([('payment_id', '=', rec.id), ('move_type', '=', 'entry')], limit=1)
            if rec.move_id.id == journal_entry.id:
                journal_entry.state = 'posted'
            # rec.state = 'gs_posted'





