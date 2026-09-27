from odoo import models


class PartnerLedgerXlsx(models.AbstractModel):
    _name = 'report.accounting_customs.partner_ledger_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet('Partner Ledger')

        bold = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })

        money = workbook.add_format({
            'num_format': '#,##0.00',
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
        })

        text_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
        })

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
        })

        period_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
        })

        total_label_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#E6F6F4',
        })

        total_format = workbook.add_format({
            'bold': True,
            'num_format': '#,##0.00',
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
            'bg_color': '#E6F6F4',
        })

        # Columns
        sheet.set_column('A:A', 25)  # Account
        sheet.set_column('B:B', 50)  # Partner
        sheet.set_column('C:F', 18)  # Numbers

        sheet.set_row(0, 25)
        sheet.set_row(1, 22)
        sheet.set_row(3, 22)

        # Header in one cell, not merged, centered inside Partner column
        sheet.write(0, 1, 'Partner Ledger Report', title_format)

        date_from = wizard.date_from.strftime('%d-%m-%Y') if wizard.date_from else ''
        date_to = wizard.date_to.strftime('%d-%m-%Y') if wizard.date_to else ''
        period_text = 'Period: %s to %s' % (date_from, date_to)

        sheet.write(1, 1, period_text, period_format)

        row = 3

        # Table headers
        sheet.write(row, 0, 'Account', bold)
        sheet.write(row, 1, 'Partner', bold)
        sheet.write(row, 2, 'Initial Balance', bold)
        sheet.write(row, 3, 'Debit', bold)
        sheet.write(row, 4, 'Credit', bold)
        sheet.write(row, 5, 'Balance', bold)

        row += 1

        Account = self.env['account.account']
        Partner = self.env['res.partner'].with_context(active_test=False)

        accounts = wizard.account_ids or Account.search([])

        # Include archived partners also.
        # If partners are selected manually, use selected partners.
        # If not selected, get all active/archived partners that have posted move lines
        # before or during the selected period.
        if wizard.partner_ids:
            partners = wizard.partner_ids.with_context(active_test=False)
        else:
            account_condition = ""
            date_condition = ""
            params = []

            if accounts:
                account_condition = "AND aml.account_id = ANY(%s)"
                params.append(accounts.ids)

            if wizard.date_to:
                date_condition = "AND aml.date <= %s"
                params.append(wizard.date_to)

            query = """
                SELECT DISTINCT aml.partner_id
                FROM account_move_line aml
                WHERE aml.partner_id IS NOT NULL
                  AND aml.parent_state = 'posted'
                  %s
                  %s
            """ % (account_condition, date_condition)

            self.env.cr.execute(query, tuple(params))
            partner_ids = [res[0] for res in self.env.cr.fetchall() if res[0]]

            partners = Partner.browse(partner_ids)

        total_initial = 0.0
        total_debit = 0.0
        total_credit = 0.0
        total_balance = 0.0

        for partner in partners:
            for account in accounts:
                # Initial Balance: before date_from
                if wizard.date_from:
                    self.env.cr.execute("""
                        SELECT COALESCE(SUM(aml.debit - aml.credit), 0)
                        FROM account_move_line aml
                        WHERE aml.partner_id = %s
                          AND aml.account_id = %s
                          AND aml.date < %s
                          AND aml.parent_state = 'posted'
                    """, (partner.id, account.id, wizard.date_from))
                    initial_balance = self.env.cr.fetchone()[0] or 0.0
                else:
                    initial_balance = 0.0

                # Debit / Credit inside selected period
                period_conditions = """
                    aml.partner_id = %s
                    AND aml.account_id = %s
                    AND aml.parent_state = 'posted'
                """
                params = [partner.id, account.id]

                if wizard.date_from:
                    period_conditions += " AND aml.date >= %s"
                    params.append(wizard.date_from)

                if wizard.date_to:
                    period_conditions += " AND aml.date <= %s"
                    params.append(wizard.date_to)

                self.env.cr.execute("""
                    SELECT
                        COALESCE(SUM(aml.debit), 0),
                        COALESCE(SUM(aml.credit), 0)
                    FROM account_move_line aml
                    WHERE %s
                """ % period_conditions, tuple(params))

                debit, credit = self.env.cr.fetchone()
                debit = debit or 0.0
                credit = credit or 0.0

                balance = initial_balance + debit - credit

                if not (initial_balance or debit or credit):
                    continue

                total_initial += initial_balance
                total_debit += debit
                total_credit += credit
                total_balance += balance

                sheet.write(row, 0, account.display_name or '', text_format)
                sheet.write(row, 1, partner.display_name or partner.name or '', text_format)
                sheet.write(row, 2, initial_balance, money)
                sheet.write(row, 3, debit, money)
                sheet.write(row, 4, credit, money)
                sheet.write(row, 5, balance, money)

                row += 1

        # Total row
        sheet.write(row, 0, 'TOTAL', total_label_format)
        sheet.write(row, 1, '', total_label_format)
        sheet.write(row, 2, total_initial, total_format)
        sheet.write(row, 3, total_debit, total_format)
        sheet.write(row, 4, total_credit, total_format)
        sheet.write(row, 5, total_balance, total_format)