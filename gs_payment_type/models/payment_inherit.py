# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    payment_type_ids = fields.Many2many("gs.account.payment.type", "payment_type_ids01", "payment_type_ids001",
                                        "payment_type_ids0001", string="Partner Type")


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    payment_type_id = fields.Many2one('gs.account.payment.type', string='Payment Type',)


    def create_draft_journal(self):
        if not self.move_id:
           self._generate_journal_entry()
           self.state = 'draft'
    def _generate_move_vals(self, write_off_line_vals=None, force_balance=None, line_ids=None):
        res = super()._generate_move_vals(write_off_line_vals, force_balance, line_ids)
        res.update({
            'branch_id': self.branch_id.id,
        })
        return res

    @api.onchange('payment_type_id')
    def onchange_partner_id_method00(self):
        for rec in self:
            if rec.state == 'draft':
                rec.partner_id = None
                # rec._prepare_move_line_default_vals

    @api.depends('journal_id', 'partner_id', 'partner_type', 'payment_type_id')
    def _compute_destination_account_id(self):
        self.destination_account_id = False
        if not self.payment_type_id:
            for pay in self:

                if pay.partner_type == 'customer':
                    # Receive money from invoice or send money to refund it.
                    if pay.partner_id:
                        pay.destination_account_id = pay.partner_id.with_company(pay.company_id).property_account_receivable_id
                    else:
                        pay.destination_account_id = self.env['account.account'].search([
                            ('company_ids', 'in', [pay.company_id.id]),
                            ('account_type', '=', 'asset_receivable'),
                            ('deprecated', '=', False),
                        ], limit=1)
                elif pay.partner_type == 'supplier':
                    # Send money to pay a bill or receive money to refund it.
                    if pay.partner_id:
                        pay.destination_account_id = pay.partner_id.with_company(pay.company_id).property_account_payable_id
                    else:
                        pay.destination_account_id = self.env['account.account'].search([
                            ('company_ids', 'in', [pay.company_id.id]),
                            ('account_type', '=', 'liability_payable'),
                            ('deprecated', '=', False),
                        ], limit=1)
        else:
            payment_type = self.env['gs.account.payment.type'].search([('id', '=', self.payment_type_id.id)])
            for payment in payment_type:
                self.destination_account_id = None
                self.destination_account_id = payment.destination_account_id.id

    @api.onchange('partner_type')
    def onchange_partner_type_method001(self):
        for rec in self:
            # test
            if rec.partner_type == 'customer':
                line = []
                partner = self.env['res.partner'].search([('customer', '=', True)])
                for p in partner:
                    line.append(p.id)
                domain = {'partner_id': [('id', 'in', line)]}
                return {'domain': domain}
            else:
                line2 = []
                partner2 = self.env['res.partner'].search([('supplier', '=', True)])
                for p2 in partner2:
                    line2.append(p2.id)
                domain = {'partner_id': [('id', 'in', line2)]}
                return {'domain': domain}

    @api.onchange('partner_type')
    def onchange_partner_id_method(self):
        for rec in self:
            if rec.partner_type:
                line = []
                payment_type = self.env['gs.account.payment.type'].search([('partner_type', '=', rec.partner_type)])
                for payment in payment_type:
                    line.append(payment.id)
                domain = {'payment_type_id': [('id', 'in', line)]}
                rec.destination_account_id = None
                return {'domain': domain}

            else:
                rec.destination_account_id = None

    @api.onchange('payment_type_id')
    def onchange_partner_id_method2(self):
        for rec in self:
            if rec.payment_type_id:
                destination = []
                payment_type = self.env['gs.account.payment.type'].search([('id', '=', rec.payment_type_id.id)])
                for payment in payment_type:
                    rec.destination_account_id = None
                    rec.destination_account_id = payment.destination_account_id.id
                    destination.append(payment.destination_account_id.id)
                domain1 = {'destination_account_id': [('id', 'in', destination)]}
                # rec.destination_account_id = None
                return {'domain': domain1}

            else:
                rec.destination_account_id = None
