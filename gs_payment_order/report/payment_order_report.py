# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api, _
from num2words import num2words


class ExteriorPurchaseOrderView(models.AbstractModel):
    _name = "report.gs_payment_order.gs_payment_order_report"
    _description = "Payment Order Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = []
        docs2 = []
        state = {'draft': 'Draft',
                 'submit': 'Submitted',
                 'approve': 'Approved',
                 'refused': 'refused',
                 }
        payment_order = self.env['gs.payment.order'].search([('id', '=', docids)])

        for child_ids in payment_order.approval_info_line:
            docs2.append({
                'level': child_ids.level,
                'status': child_ids.status,
                'approval_date': child_ids.approval_date,
                'approved_by': child_ids.approved_by.name,

            })
        for payment in payment_order:
            num_word = ''
            if self.env.lang == 'en_US':
                num_word = num2words(payment.amount, lang='en_US') + _(" only")
            if self.env.lang == 'ar_001':
                num_word = num2words(payment.amount, lang='ar_001') + _(" فقط ")

            return {
                'docs2': docs2,

                'partner_id': payment.partner_id.name if payment.partner_id.name else " ",
                'email': payment.partner_id.email if payment.partner_id.email else " ",
                'phone': payment.partner_id.phone if payment.partner_id.phone else " ",

                'name': payment.name if payment.name else " ",
                'currency_id': payment.currency_id.name if payment.currency_id.name else " ",
                'payment_type_id': payment.payment_type_id.name if payment.payment_type_id.name else " ",
                'journal_id': payment.journal_id.name if payment.journal_id.name else " ",
                'create_date': payment.create_date if payment.create_date else " ",
                'payment_due_date': payment.payment_due_date if payment.payment_due_date else " ",
                'company_name': payment.company_id.name if payment.company_id.name else " ",
                'user_id': payment.user_id.name if payment.user_id.name else " ",
                'description': payment.description if payment.description else " ",
                'amount': payment.amount if payment.amount else " ",
                'exchange_rate': payment.exchange_rate if payment.exchange_rate else " ",
                'state': state[payment.state],

                'num_word': num_word,

            }
