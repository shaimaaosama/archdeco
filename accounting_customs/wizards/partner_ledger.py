# -*- coding: utf-8 -*-

import re

from odoo import models, fields


class PartnerLedgerXlsxWizard(models.TransientModel):
    _name = 'partner.ledger.xlsx.wizard'
    _description = 'Partner Ledger Excel Wizard'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    partner_ids = fields.Many2many('res.partner', string="Partners")
    account_ids = fields.Many2many('account.account', string="Accounts")

    def _clean_xlsx_filename_part(self, value):
        value = value or ''

        # Remove characters not allowed in file names
        value = re.sub(r'[\\/*?:\[\]<>|"]', '-', value)

        # Remove duplicated spaces
        value = re.sub(r'\s+', ' ', value).strip()

        return value

    def get_xlsx_report_filename(self):
        self.ensure_one()

        account_parts = []

        if self.account_ids:
            for account in self.account_ids:
                code = account.code or ''
                name = account.name or ''

                if code and name:
                    account_label = '%s %s' % (code, name)
                elif code:
                    account_label = code
                else:
                    account_label = name

                account_parts.append(
                    self._clean_xlsx_filename_part(account_label)
                )

            accounts_text = ' - '.join(account_parts)
        else:
            accounts_text = 'All Accounts'

        date_from = self.date_from.strftime('%d-%m-%Y') if self.date_from else ''
        date_to = self.date_to.strftime('%d-%m-%Y') if self.date_to else ''

        filename = 'Partner Ledger - %s - %s to %s' % (
            accounts_text,
            date_from,
            date_to,
        )

        # Avoid very long file name if many accounts are selected
        if len(filename) > 180:
            filename = filename[:180].rstrip(' -')

        return filename

    def action_print_excel(self):
        self.ensure_one()
        return self.env.ref(
            'accounting_customs.partner_ledger_xlsx_report'
        ).report_action(self)