from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, float_round, format_date, groupby
from odoo.fields import Command
from datetime import date, datetime
from odoo.exceptions import AccessError, UserError, ValidationError


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    move_ids = fields.Many2many('account.move', 'move_ids01', 'move_ids001', 'move_ids0001', string='RO Invoices')


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    mm_move_id = fields.Many2one('account.move')
    gs_is_create = fields.Boolean(copy=False)
    credit_note_ids = fields.Many2many('account.move', string='Credit Note', copy=False)
    credit_note_count = fields.Integer(compute="_compute_credit_note_count")

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrderInherit, self)._prepare_invoice()
        is_create = False
        print("kkkkkkkklllllllllllllllllllldddddddddddddddddddddddddddddddddddddjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjssssssssssssssssssssssssssssssssssssssssssssssssdkkkkkk")
        for line in self.order_line:
            if not is_create:
                if line.product_uom_qty < 0:
                    if line.mm_move_id and line.reason_id:
                        invoice_vals.update({
                            'ref': _('Reversal of: %(move_name)s, %(reason)s', move_name=line.mm_move_id.name,
                                     reason=line.reason_id.name + ',' + line.order_id.name),
                            'reversed_entry_id': line.mm_move_id.id,
                        })
        return invoice_vals

    # def _prepare_invoice(self):
    #     """
    #     Prepare the dict of values to create the new invoice for a sales order. This method may be
    #     overridden to implement custom invoice generation (making sure to call super() to establish
    #     a clean extension chain).
    #     """
    #     self.ensure_one()
    #     print("2222222222222222")
    #     journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
    #     if not journal:
    #         raise UserError(_('Please define an accounting sales journal for the company %s (%s).', self.company_id.name, self.company_id.id))
    #     for rec in self:
    #         is_create = False
    #         for line in rec.order_line:
    #             if not is_create:
    #                 if line.product_uom_qty < 0:
    #                     if line.mm_move_id and line.reason_id:
    #                         values = {
    #                             'ref': _('Reversal of: %(move_name)s, %(reason)s', move_name=line.mm_move_id.name,
    #                                      reason=line.reason_id.name + ',' + line.order_id.name),
    #                             'reversed_entry_id': line.mm_move_id.id,
    #                             'move_type': 'out_invoice',
    #                             'narration': self.note,
    #                             'currency_id': self.pricelist_id.currency_id.id,
    #                             'campaign_id': self.campaign_id.id,
    #                             'medium_id': self.medium_id.id,
    #                             'source_id': self.source_id.id,
    #                             'user_id': self.user_id.id,
    #                             'invoice_user_id': self.user_id.id,
    #                             'team_id': self.team_id.id,
    #                             'partner_id': self.partner_invoice_id.id,
    #                             'partner_shipping_id': self.partner_shipping_id.id,
    #                             'fiscal_position_id': (
    #                                         self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(
    #                                     self.partner_invoice_id.id)).id,
    #                             'partner_bank_id': self.company_id.partner_id.bank_ids.filtered(
    #                                 lambda bank: bank.company_id.id in (self.company_id.id, False))[:1].id,
    #                             'journal_id': journal.id,  # company comes from the journal
    #                             'invoice_origin': self.name,
    #                             'invoice_payment_term_id': self.payment_term_id.id,
    #                             'payment_reference': self.reference,
    #                             'transaction_ids': [(6, 0, self.transaction_ids.ids)],
    #                             'invoice_line_ids': [],
    #                             'company_id': self.company_id.id,
    #                         }
    #                         is_create = True
    #                         return values
    #                     else:
    #                         raise ValidationError("Add Invoice & Reason")
    #
    #                 else:
    #                     values = {
    #                         'ref': self.client_order_ref or '',
    #                         'move_type': 'out_invoice',
    #                         'narration': self.note,
    #                         'currency_id': self.pricelist_id.currency_id.id,
    #                         'campaign_id': self.campaign_id.id,
    #                         'medium_id': self.medium_id.id,
    #                         'source_id': self.source_id.id,
    #                         'user_id': self.user_id.id,
    #                         'invoice_user_id': self.user_id.id,
    #                         'team_id': self.team_id.id,
    #                         'partner_id': self.partner_invoice_id.id,
    #                         'partner_shipping_id': self.partner_shipping_id.id,
    #                         'fiscal_position_id': (
    #                                     self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(
    #                                 self.partner_invoice_id.id)).id,
    #                         'partner_bank_id': self.company_id.partner_id.bank_ids.filtered(
    #                             lambda bank: bank.company_id.id in (self.company_id.id, False))[:1].id,
    #                         'journal_id': journal.id,  # company comes from the journal
    #                         'invoice_origin': self.name,
    #                         'invoice_payment_term_id': self.payment_term_id.id,
    #                         'payment_reference': self.reference,
    #                         'transaction_ids': [(6, 0, self.transaction_ids.ids)],
    #                         'invoice_line_ids': [],
    #                         'company_id': self.company_id.id,
    #                     }
    #                     return values

    def action_create_one_credit_note(self):
        for rec in self:
            is_create = False
            for line in rec.order_line:
                if not is_create:
                    if line.mm_move_id and line.reason_id:
                        vals = {
                            'ref': _('Reversal of: %(move_name)s, %(reason)s', move_name=line.mm_move_id.name,
                                     reason=line.reason_id.name + ',' + line.order_id.name),
                            'move_type': 'out_refund',
                            'partner_id': rec.partner_id.id,
                            'company_id': rec.company_id.id,
                            'reversed_entry_id': line.mm_move_id.id,
                        }
                        entry = self.env['account.move'].create(vals)
                        rec.mm_move_id = entry.id
                        is_create = True
                    else:
                        raise ValidationError("Add Invoice & Reason")
                if rec.mm_move_id:
                    lst = []
                    val = (0, 0, {
                        'product_id': line.product_id.id,
                        'quantity': line.product_uom_qty,
                        "product_uom_id": line.product_uom.id,
                    })
                    lst.append(val)
                    rec.mm_move_id.invoice_line_ids = lst
                    rec.mm_move_id.move_ids = [(4, line.mm_move_id.id, 0)]
                    rec.credit_note_ids = [(4, rec.mm_move_id.id, 0)]
                    rec.gs_is_create = True

    def _compute_credit_note_count(self):
        for rec in self:
            rec.credit_note_count = 0
            if rec.credit_note_ids:
                rec.credit_note_count = len(rec.credit_note_ids.ids)

    def action_view_credit_note(self):
        action = self.env.ref('account.action_move_out_refund_type').sudo().read()[0]

        credit_notes = self.mapped("credit_note_ids")
        if len(credit_notes) > 1:
            action['domain'] = [('id', 'in', credit_notes.ids)]
        elif credit_notes:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = credit_notes.id
        return action


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    reason_id = fields.Many2one('gs.reason', string='Reason',)
    mm_move_id = fields.Many2one('account.move', string='Invoice',)
    partner_id = fields.Many2one("res.partner", string="Customer", related='order_id.partner_id')
