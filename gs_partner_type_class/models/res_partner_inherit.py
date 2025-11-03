# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError


class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    partner_type_ids = fields.Many2many("gs.partner.type", "partner_type_ids_gpt01", "partner_type_ids_gpt001",
                                        "partner_type_ids_gpt0001", string="Partner Type")


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _onchange_partner_id2(self):
        res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])
        return {'domain': {'partner_id': [('partner_type', 'in', res_user.partner_type_ids.ids)]}}


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    @api.onchange('partner_id')
    def _onchange_partner_id2(self):
        res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])
        return {'domain': {'partner_id': [('partner_type', 'in', res_user.partner_type_ids.ids)]}}


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    @api.onchange('partner_id')
    def _onchange_partner_id2(self):
        res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])
        return {'domain': {'partner_id': [('partner_type', 'in', res_user.partner_type_ids.ids)]}}

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self = self.with_company(self.journal_id.company_id)

            warning = {}
            if self.partner_id:
                rec_account = self.partner_id.property_account_receivable_id
                pay_account = self.partner_id.property_account_payable_id
                if not rec_account and not pay_account:
                    action = self.env.ref('account.action_account_config')
                    msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                    raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))
                p = self.partner_id
                if p.invoice_warn == 'no-message' and p.parent_id:
                    p = p.parent_id
                if p.invoice_warn and p.invoice_warn != 'no-message':
                    # Block if partner only has warning but parent company is blocked
                    if p.invoice_warn != 'block' and p.parent_id and p.parent_id.invoice_warn == 'block':
                        p = p.parent_id
                    warning = {
                        'title': _("Warning for %s", p.name),
                        'message': p.invoice_warn_msg
                    }
                    if p.invoice_warn == 'block':
                        self.partner_id = False
                        return {'warning': warning}

            if self.is_sale_document(include_receipts=True) and self.partner_id:
                self.invoice_payment_term_id = self.partner_id.property_payment_term_id or self.invoice_payment_term_id
                new_term_account = self.partner_id.commercial_partner_id.property_account_receivable_id
            elif self.is_purchase_document(include_receipts=True) and self.partner_id:
                self.invoice_payment_term_id = self.partner_id.property_supplier_payment_term_id or self.invoice_payment_term_id
                new_term_account = self.partner_id.commercial_partner_id.property_account_payable_id
            else:
                new_term_account = None

            for line in self.line_ids:
                line.partner_id = self.partner_id.commercial_partner_id

                if new_term_account and line.account_id.user_type_id.type in ('receivable', 'payable'):
                    line.account_id = new_term_account

            self._compute_bank_partner_id()
            bank_ids = self.bank_partner_id.bank_ids.filtered(lambda bank: bank.company_id is False or bank.company_id == self.company_id)
            self.partner_bank_id = bank_ids and bank_ids[0]

            # Find the new fiscal position.
            delivery_partner_id = self._get_invoice_delivery_partner_id()
            self.fiscal_position_id = self.env['account.fiscal.position'].get_fiscal_position(
                self.partner_id.id, delivery_id=delivery_partner_id)
            self._recompute_dynamic_lines()
            if warning:
                return {'warning': warning}


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    partner_type = fields.Many2one('gs.partner.type', string='Partner Type')
    partner_class = fields.Many2one('gs.partner.class', string='Partner Class')
    run_compute_boolean = fields.Boolean(compute="_compute_run",)
    run_compute = fields.Integer()

    def _compute_run(self):
        for rec in self:
            rec.run_compute += 1
            if rec.run_compute == 1000:
                rec.run_compute = 0
            if not rec.run_compute_boolean:
                rec.run_compute_boolean = True
            else:
                rec.run_compute_boolean = False


class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    partner_type_id = fields.Many2one('gs.partner.type', related='partner_id.partner_type', store=True)
    partner_class_id = fields.Many2one('gs.partner.class', related='partner_id.partner_class', store=True)