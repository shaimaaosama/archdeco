# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _
from odoo.tools import get_lang, SQL


class AccountPartnerLedger(models.AbstractModel):
    _inherit = 'account.partner.ledger.report.handler'

    @api.model
    def _get_options_domain(self, options):
        domain = super(AccountPartnerLedger, self)._get_options_domain(options)
        domain += self._get_options_branch_domain()
        return domain

    @api.model
    def _get_options_branch_domain(self, options):
        domain = []
        if options.get('branch_ids'):
            branch_ids = [int(branch) for branch in options['branch_ids']]
            domain.append(('branch_id', 'in', branch_ids))
        return domain

    # def _get_aml_values(self, options, partner_ids, offset=0, limit=None):
    #     rslt = {partner_id: [] for partner_id in partner_ids}
    #
    #     partner_ids_wo_none = [x for x in partner_ids if x]
    #     directly_linked_aml_partner_clauses = []
    #     directly_linked_aml_partner_params = []
    #     indirectly_linked_aml_partner_params = []
    #     indirectly_linked_aml_partner_clause = 'aml_with_partner.partner_id IS NOT NULL'
    #     if None in partner_ids:
    #         directly_linked_aml_partner_clauses.append('account_move_line.partner_id IS NULL')
    #     if partner_ids_wo_none:
    #         directly_linked_aml_partner_clauses.append('account_move_line.partner_id IN %s')
    #         directly_linked_aml_partner_params.append(tuple(partner_ids_wo_none))
    #         indirectly_linked_aml_partner_clause = 'aml_with_partner.partner_id IN %s'
    #         indirectly_linked_aml_partner_params.append(tuple(partner_ids_wo_none))
    #     directly_linked_aml_partner_clause = '(' + ' OR '.join(directly_linked_aml_partner_clauses) + ')'
    #
    #     ct_query = self.env['account.report']._get_currency_table(options)
    #     queries = []
    #     all_params = []
    #     lang = self.env.lang or get_lang(self.env).code
    #     journal_name = f"COALESCE(journal.name->>'{lang}', journal.name->>'en_US')" if \
    #         self.pool['account.journal'].name.translate else 'journal.name'
    #     account_name = f"COALESCE(account.name->>'{lang}', account.name->>'en_US')" if \
    #         self.pool['account.account'].name.translate else 'account.name'
    #     report = self.env.ref('account_reports.partner_ledger_report')
    #     for column_group_key, group_options in report._split_options_per_column_group(options).items():
    #         tables, where_clause, where_params = report._get_report_query(group_options, 'strict_range')
    #
    #         all_params += [
    #             column_group_key,
    #             *where_params,
    #             *directly_linked_aml_partner_params,
    #             column_group_key,
    #             *indirectly_linked_aml_partner_params,
    #             *where_params,
    #             group_options['date']['date_from'],
    #             group_options['date']['date_to'],
    #         ]
    #
    #         # For the move lines directly linked to this partner
    #         queries.append(f'''
    #             SELECT
    #                 account_move_line.id,
    #                 account_move_line.date_maturity,
    #                 account_move_line.name,
    #                 account_move_line.ref,
    #                 account_move_line.company_id,
    #                 account_move_line.account_id,
    #                 account_move_line.payment_id,
    #                 account_move_line.partner_id,
    #                 account_move_line.currency_id,
    #                 account_move_line.amount_currency,
    #                 account_move_line.matching_number,
    #                 COALESCE(account_move_line.invoice_date, account_move_line.date)                 AS invoice_date,
    #                 ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)   AS debit,
    #                 ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)  AS credit,
    #                 ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,
    #                 account_move.name                                                                AS move_name,
    #                 account_move.move_type                                                           AS move_type,
    #                 account.code                                                                     AS account_code,
    #                 {account_name}                                                                   AS account_name,
    #                 journal.code                                                                     AS journal_code,
    #                 {journal_name}                                                                   AS journal_name,
    #                 branch.name                                                                      AS branch_name,
    #                 %s                                                                               AS column_group_key,
    #                 'directly_linked_aml'                                                            AS key
    #             FROM {tables}
    #             JOIN account_move ON account_move.id = account_move_line.move_id
    #             LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
    #             LEFT JOIN res_company company               ON company.id = account_move_line.company_id
    #             LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
    #             LEFT JOIN account_account account           ON account.id = account_move_line.account_id
    #             LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
    #             LEFT JOIN res_branch branch                 ON branch.id = account_move_line.branch_id
    #             WHERE {where_clause} AND {directly_linked_aml_partner_clause}
    #             ORDER BY account_move_line.date, account_move_line.id
    #         ''')
    #
    #         # For the move lines linked to no partner, but reconciled with this partner. They will appear in grey in the report
    #         queries.append(f'''
    #             SELECT
    #                 account_move_line.id,
    #                 account_move_line.date_maturity,
    #                 account_move_line.name,
    #                 account_move_line.ref,
    #                 account_move_line.company_id,
    #                 account_move_line.account_id,
    #                 account_move_line.payment_id,
    #                 aml_with_partner.partner_id,
    #                 account_move_line.currency_id,
    #                 account_move_line.amount_currency,
    #                 account_move_line.matching_number,
    #                 COALESCE(account_move_line.invoice_date, account_move_line.date)                    AS invoice_date,
    #                 CASE WHEN aml_with_partner.balance > 0 THEN 0 ELSE ROUND(
    #                     partial.amount * currency_table.rate, currency_table.precision
    #                 ) END                                                                               AS debit,
    #                 CASE WHEN aml_with_partner.balance < 0 THEN 0 ELSE ROUND(
    #                     partial.amount * currency_table.rate, currency_table.precision
    #                 ) END                                                                               AS credit,
    #                 - sign(aml_with_partner.balance) * ROUND(
    #                     partial.amount * currency_table.rate, currency_table.precision
    #                 )                                                                                   AS balance,
    #                 account_move.name                                                                   AS move_name,
    #                 account_move.move_type                                                              AS move_type,
    #                 account.code                                                                        AS account_code,
    #                 {account_name}                                                                      AS account_name,
    #                 journal.code                                                                        AS journal_code,
    #                 {journal_name}                                                                      AS journal_name,
    #                 branch.name                                                                         AS branch_name,
    #                 %s                                                                                  AS column_group_key,
    #                 'indirectly_linked_aml'                                                             AS key
    #             FROM {tables}
    #                 LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id,
    #                 account_partial_reconcile partial,
    #                 account_move,
    #                 account_move_line aml_with_partner,
    #                 account_journal journal,
    #                 account_account account,
    #                 res_branch branch
    #             WHERE
    #                 (account_move_line.id = partial.debit_move_id OR account_move_line.id = partial.credit_move_id)
    #                 AND account_move_line.partner_id IS NULL
    #                 AND account_move.id = account_move_line.move_id
    #                 AND (aml_with_partner.id = partial.debit_move_id OR aml_with_partner.id = partial.credit_move_id)
    #                 AND {indirectly_linked_aml_partner_clause}
    #                 AND journal.id = account_move_line.journal_id
    #                 AND account.id = account_move_line.account_id
    #                 AND {where_clause}
    #                 AND partial.max_date BETWEEN %s AND %s
    #                 AND branch.id = account_move_line.branch_id
    #             ORDER BY account_move_line.date, account_move_line.id
    #         ''')
    #
    #     query = '(' + ') UNION ALL ('.join(queries) + ')'
    #
    #     if offset:
    #         query += ' OFFSET %s '
    #         all_params.append(offset)
    #
    #     if limit:
    #         query += ' LIMIT %s '
    #         all_params.append(limit)
    #
    #     self._cr.execute(query, all_params)
    #     for aml_result in self._cr.dictfetchall():
    #         if aml_result['key'] == 'indirectly_linked_aml':
    #
    #             # Append the line to the partner found through the reconciliation.
    #             if aml_result['partner_id'] in rslt:
    #                 rslt[aml_result['partner_id']].append(aml_result)
    #
    #             # Balance it with an additional line in the Unknown Partner section but having reversed amounts.
    #             if None in rslt:
    #                 rslt[None].append({
    #                     **aml_result,
    #                     'debit': aml_result['credit'],
    #                     'credit': aml_result['debit'],
    #                     'balance': -aml_result['balance'],
    #                 })
    #         else:
    #             rslt[aml_result['partner_id']].append(aml_result)
    #
    #     return rslt

    def _get_aml_values(self, options, partner_ids, offset=0, limit=None):
        rslt = {partner_id: [] for partner_id in partner_ids}

        partner_ids_wo_none = [x for x in partner_ids if x]
        directly_linked_aml_partner_clauses = []
        indirectly_linked_aml_partner_clause = SQL('aml_with_partner.partner_id IS NOT NULL')
        if None in partner_ids:
            directly_linked_aml_partner_clauses.append(SQL('account_move_line.partner_id IS NULL'))
        if partner_ids_wo_none:
            directly_linked_aml_partner_clauses.append(
                SQL('account_move_line.partner_id IN %s', tuple(partner_ids_wo_none)))
            indirectly_linked_aml_partner_clause = SQL('aml_with_partner.partner_id IN %s', tuple(partner_ids_wo_none))
        directly_linked_aml_partner_clause = SQL('(%s)', SQL(' OR ').join(directly_linked_aml_partner_clauses))

        queries = []
        journal_name = self.env['account.journal']._field_to_sql('journal', 'name')
        report = self.env.ref('account_reports.partner_ledger_report')
        additional_columns = self._get_additional_column_aml_values()
        order_by = self._get_order_by_aml_values()
        for column_group_key, group_options in report._split_options_per_column_group(options).items():
            query = report._get_report_query(group_options, 'strict_range')
            account_alias = query.left_join(lhs_alias='account_move_line', lhs_column='account_id',
                                            rhs_table='account_account', rhs_column='id', link='account_id')
            account_code = self.env['account.account']._field_to_sql(account_alias, 'code', query)
            account_name = self.env['account.account']._field_to_sql(account_alias, 'name')

            # For the move lines directly linked to this partner
            # ruff: noqa: FURB113
            queries.append(SQL(
                '''
                SELECT
                    account_move_line.id,
                    COALESCE(account_move_line.date_maturity, account_move_line.date) AS date_maturity,
                    account_move_line.name,
                    account_move_line.ref,
                    account_move_line.company_id,
                    account_move_line.account_id,
                    account_move_line.payment_id,
                    account_move_line.partner_id,
                    account_move_line.currency_id,
                    account_move_line.amount_currency,
                    account_move_line.matching_number,
                    %(additional_columns)s
                    COALESCE(account_move_line.invoice_date, account_move_line.date) AS invoice_date,
                    %(debit_select)s                                                 AS debit,
                    %(credit_select)s                                                AS credit,
                    %(balance_select)s                                               AS amount,
                    %(balance_select)s                                               AS balance,
                    account_move.name                                                AS move_name,
                    account_move.move_type                                           AS move_type,
                    %(account_code)s                                                 AS account_code,
                    %(account_name)s                                                 AS account_name,
                    journal.code                                                     AS journal_code,
                    %(journal_name)s                                                 AS journal_name,
                    branch.name                                                                      AS branch_name,                    

                    %(column_group_key)s                                             AS column_group_key,
                    'directly_linked_aml'                                            AS key,
                    0                                                                AS partial_id
                FROM %(table_references)s
                JOIN account_move ON account_move.id = account_move_line.move_id
                %(currency_table_join)s
                LEFT JOIN res_company company               ON company.id = account_move_line.company_id
                LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
                LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
                LEFT JOIN res_branch branch                 ON branch.id = account_move_line.branch_id                

                WHERE %(search_condition)s AND %(directly_linked_aml_partner_clause)s

                ORDER BY %(order_by)s
                ''',
                additional_columns=additional_columns,
                debit_select=report._currency_table_apply_rate(SQL("account_move_line.debit")),
                credit_select=report._currency_table_apply_rate(SQL("account_move_line.credit")),
                balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                account_code=account_code,
                account_name=account_name,
                journal_name=journal_name,
                column_group_key=column_group_key,
                table_references=query.from_clause,
                currency_table_join=report._currency_table_aml_join(group_options),
                search_condition=query.where_clause,
                directly_linked_aml_partner_clause=directly_linked_aml_partner_clause,
                order_by=order_by,
            ))

            # For the move lines linked to no partner, but reconciled with this partner. They will appear in grey in the report
            queries.append(SQL(
                '''
                SELECT
                    account_move_line.id,
                    COALESCE(account_move_line.date_maturity, account_move_line.date) AS date_maturity,
                    account_move_line.name,
                    account_move_line.ref,
                    account_move_line.company_id,
                    account_move_line.account_id,
                    account_move_line.payment_id,
                    aml_with_partner.partner_id,
                    account_move_line.currency_id,
                    account_move_line.amount_currency,
                    account_move_line.matching_number,
                    %(additional_columns)s
                    COALESCE(account_move_line.invoice_date, account_move_line.date) AS invoice_date,
                    %(debit_select)s                                                 AS debit,
                    %(credit_select)s                                                AS credit,
                    %(balance_select)s                                               AS amount,
                    %(balance_select)s                                               AS balance,
                    account_move.name                                                AS move_name,
                    account_move.move_type                                           AS move_type,
                    %(account_code)s                                                 AS account_code,
                    %(account_name)s                                                 AS account_name,
                    journal.code                                                     AS journal_code,
                    %(journal_name)s                                                 AS journal_name,
                    branch.name                                                                      AS branch_name,
                    %(column_group_key)s                                             AS column_group_key,
                    'indirectly_linked_aml'                                          AS key,
                    partial.id                                                       AS partial_id
                FROM %(table_references)s
                    %(currency_table_join)s,
                    account_partial_reconcile partial,
                    account_move,
                    account_move_line aml_with_partner,
                    account_journal journal,
                    res_branch branch

                WHERE
                    (account_move_line.id = partial.debit_move_id OR account_move_line.id = partial.credit_move_id)
                    AND account_move_line.partner_id IS NULL
                    AND account_move.id = account_move_line.move_id
                    AND (aml_with_partner.id = partial.debit_move_id OR aml_with_partner.id = partial.credit_move_id)
                    AND %(indirectly_linked_aml_partner_clause)s
                    AND journal.id = account_move_line.journal_id
                    AND %(account_alias)s.id = account_move_line.account_id
                    AND %(search_condition)s
                    AND partial.max_date BETWEEN %(date_from)s AND %(date_to)s
                    AND branch.id = account_move_line.branch_id
                ORDER BY %(order_by)s
                ''',
                additional_columns=additional_columns,
                debit_select=report._currency_table_apply_rate(
                    SQL("CASE WHEN aml_with_partner.balance > 0 THEN 0 ELSE partial.amount END")),
                credit_select=report._currency_table_apply_rate(
                    SQL("CASE WHEN aml_with_partner.balance < 0 THEN 0 ELSE partial.amount END")),
                balance_select=report._currency_table_apply_rate(
                    SQL("-SIGN(aml_with_partner.balance) * partial.amount")),
                account_code=account_code,
                account_name=account_name,
                journal_name=journal_name,
                column_group_key=column_group_key,
                table_references=query.from_clause,
                currency_table_join=report._currency_table_aml_join(group_options),
                indirectly_linked_aml_partner_clause=indirectly_linked_aml_partner_clause,
                account_alias=SQL.identifier(account_alias),
                search_condition=query.where_clause,
                date_from=group_options['date']['date_from'],
                date_to=group_options['date']['date_to'],
                order_by=order_by,
            ))

        query = SQL(" UNION ALL ").join(SQL("(%s)", query) for query in queries)

        if offset:
            query = SQL('%s OFFSET %s ', query, offset)

        if limit:
            query = SQL('%s LIMIT %s ', query, limit)

        self._cr.execute(query)
        for aml_result in self._cr.dictfetchall():
            if aml_result['key'] == 'indirectly_linked_aml':

                # Append the line to the partner found through the reconciliation.
                if aml_result['partner_id'] in rslt:
                    rslt[aml_result['partner_id']].append(aml_result)

                # Balance it with an additional line in the Unknown Partner section but having reversed amounts.
                if None in rslt:
                    rslt[None].append({
                        **aml_result,
                        'debit': aml_result['credit'],
                        'credit': aml_result['debit'],
                        'amount': aml_result['credit'] - aml_result['debit'],
                        'balance': -aml_result['balance'],
                    })
            else:
                rslt[aml_result['partner_id']].append(aml_result)

        return rslt
