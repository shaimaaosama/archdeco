# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools.misc import format_date, DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta


class GeneralLedgerInherit(models.AbstractModel):
    _inherit = 'account.general.ledger.report.handler'

    # @api.model
    # def _do_query(self, options_list, expanded_account=None, fetch_lines=True):
    #     ''' Execute the queries, perform all the computation and return (accounts_results, taxes_results). Both are
    #     lists of tuple (record, fetched_values) sorted by the table's model _order:
    #     - accounts_values: [(record, values), ...] where
    #         - record is an account.account record.
    #         - values is a list of dictionaries, one per period containing:
    #             - sum:                              {'debit': float, 'credit': float, 'balance': float}
    #             - (optional) initial_balance:       {'debit': float, 'credit': float, 'balance': float}
    #             - (optional) unaffected_earnings:   {'debit': float, 'credit': float, 'balance': float}
    #             - (optional) lines:                 [line_vals_1, line_vals_2, ...]
    #     - taxes_results: [(record, values), ...] where
    #         - record is an account.tax record.
    #         - values is a dictionary containing:
    #             - base_amount:  float
    #             - tax_amount:   float
    #     :param options_list:        The report options list, first one being the current dates range, others being the
    #                                 comparisons.
    #     :param expanded_account:    An optional account.account record that must be specified when expanding a line
    #                                 with of without the load more.
    #     :param fetch_lines:         A flag to fetch the account.move.lines or not (the 'lines' key in accounts_values).
    #     :return:                    (accounts_values, taxes_results)
    #     '''
    #     # Execute the queries and dispatch the results.
    #     query, params = self._get_query_sums(options_list, expanded_account=expanded_account)
    #
    #     groupby_accounts = {}
    #     groupby_companies = {}
    #     groupby_taxes = {}
    #
    #     self.env.cr.execute(query, params)
    #     for res in self._cr.dictfetchall():
    #         # No result to aggregate.
    #         if res['groupby'] is None:
    #             continue
    #
    #         i = res['period_number']
    #         key = res['key']
    #         if key == 'sum':
    #             groupby_accounts.setdefault(res['groupby'], [{} for n in range(len(options_list))])
    #             groupby_accounts[res['groupby']][i][key] = res
    #         elif key == 'initial_balance':
    #             groupby_accounts.setdefault(res['groupby'], [{} for n in range(len(options_list))])
    #             groupby_accounts[res['groupby']][i][key] = res
    #         elif key == 'unaffected_earnings':
    #             groupby_companies.setdefault(res['groupby'], [{} for n in range(len(options_list))])
    #             groupby_companies[res['groupby']][i] = res
    #         elif key == 'base_amount' and len(options_list) == 1:
    #             groupby_taxes.setdefault(res['groupby'], {})
    #             groupby_taxes[res['groupby']][key] = res['balance']
    #         elif key == 'tax_amount' and len(options_list) == 1:
    #             groupby_taxes.setdefault(res['groupby'], {})
    #             groupby_taxes[res['groupby']][key] = res['balance']
    #
    #     # Fetch the lines of unfolded accounts.
    #     # /!\ Unfolding lines combined with multiple comparisons is not supported.
    #     if fetch_lines and len(options_list) == 1:
    #         options = options_list[0]
    #         unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])
    #         if expanded_account or unfold_all or options['unfolded_lines']:
    #             query, params = self._get_query_amls(options, expanded_account)
    #             self.env.cr.execute(query, params)
    #             for res in self._cr.dictfetchall():
    #                 groupby_accounts[res['account_id']][0].setdefault('lines', [])
    #                 groupby_accounts[res['account_id']][0]['lines'].append(res)
    #
    #     # Affect the unaffected earnings to the first fetched account of type 'account.data_unaffected_earnings'.
    #     # There is an unaffected earnings for each company but it's less costly to fetch all candidate accounts in
    #     # a single search and then iterate it.
    #     if groupby_companies:
    #         unaffected_earnings_type = self.env.ref('account.data_unaffected_earnings')
    #         candidates_accounts = self.env['account.account'].search([
    #             ('user_type_id', '=', unaffected_earnings_type.id), ('company_id', 'in', list(groupby_companies.keys()))
    #         ])
    #         for account in candidates_accounts:
    #             company_unaffected_earnings = groupby_companies.get(account.company_id.id)
    #             if not company_unaffected_earnings:
    #                 continue
    #             for i in range(len(options_list)):
    #                 unaffected_earnings = company_unaffected_earnings[i]
    #                 groupby_accounts.setdefault(account.id, [{} for i in range(len(options_list))])
    #                 groupby_accounts[account.id][i]['unaffected_earnings'] = unaffected_earnings
    #             del groupby_companies[account.company_id.id]
    #
    #     # Retrieve the accounts to browse.
    #     # groupby_accounts.keys() contains all account ids affected by:
    #     # - the amls in the current period.
    #     # - the amls affecting the initial balance.
    #     # - the unaffected earnings allocation.
    #     # Note a search is done instead of a browse to preserve the table ordering.
    #     res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])
    #     if expanded_account:
    #         accounts = expanded_account
    #     elif groupby_accounts:
    #         accounts = self.env['account.account'].search([('id', 'in', list(groupby_accounts.keys())),
    #                                                        ('id', 'in', res_user.account_ids.ids)])
    #     else:
    #         accounts = []
    #     accounts_results = [(account, groupby_accounts[account.id]) for account in accounts]
    #
    #     # Fetch as well the taxes.
    #     if groupby_taxes:
    #         taxes = self.env['account.tax'].search([('id', 'in', list(groupby_taxes.keys()))])
    #     else:
    #         taxes = []
    #     taxes_results = [(tax, groupby_taxes[tax.id]) for tax in taxes]
    #     return accounts_results, taxes_results
    def _query_values(self, report, options):
        """ Executes the queries, and performs all the computations.

        :return:    [(record, values_by_column_group), ...],  where
                    - record is an account.account record.
                    - values_by_column_group is a dict in the form {column_group_key: values, ...}
                        - column_group_key is a string identifying a column group, as in options['column_groups']
                        - values is a list of dictionaries, one per period containing:
                            - sum:                              {'debit': float, 'credit': float, 'balance': float}
                            - (optional) initial_balance:       {'debit': float, 'credit': float, 'balance': float}
                            - (optional) unaffected_earnings:   {'debit': float, 'credit': float, 'balance': float}
        """
        # Execute the queries and dispatch the results.
        query = self._get_query_sums(report, options)

        if not query:
            return []

        groupby_accounts = {}
        groupby_companies = {}

        self._cr.execute(query)
        for res in self._cr.dictfetchall():
            # No result to aggregate.
            if res['groupby'] is None:
                continue

            column_group_key = res['column_group_key']
            key = res['key']
            if key == 'sum':
                groupby_accounts.setdefault(res['groupby'], {col_group_key: {} for col_group_key in options['column_groups']})
                groupby_accounts[res['groupby']][column_group_key][key] = res

            elif key == 'initial_balance':
                groupby_accounts.setdefault(res['groupby'], {col_group_key: {} for col_group_key in options['column_groups']})
                groupby_accounts[res['groupby']][column_group_key][key] = res

            elif key == 'unaffected_earnings':
                groupby_companies.setdefault(res['groupby'], {col_group_key: {} for col_group_key in options['column_groups']})
                groupby_companies[res['groupby']][column_group_key] = res

        # Affect the unaffected earnings to the first fetched account of type 'account.data_unaffected_earnings'.
        # It's less costly to fetch all candidate accounts in a single search and then iterate it.
        res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])

        if groupby_companies:
            unaffected_earnings_accounts = self.env['account.account'].search([
                ('display_name', 'ilike', options.get('filter_search_bar')),
                *self.env['account.account']._check_company_domain(list(groupby_companies.keys())),
                ('account_type', '=', 'equity_unaffected'),
            ])
            for company_id, groupby_company in groupby_companies.items():
                if equity_unaffected_account := unaffected_earnings_accounts.filtered(lambda a: self.env['res.company'].browse(company_id).root_id in a.company_ids):
                    for column_group_key in options['column_groups']:
                        groupby_accounts.setdefault(
                            equity_unaffected_account.id,
                            {col_group_key: {'unaffected_earnings': {}} for col_group_key in options['column_groups']},
                        )
                        if unaffected_earnings := groupby_company.get(column_group_key):
                            if groupby_accounts[equity_unaffected_account.id][column_group_key].get('unaffected_earnings'):
                                for key in ['amount_currency', 'debit', 'credit', 'balance']:
                                    groupby_accounts[equity_unaffected_account.id][column_group_key]['unaffected_earnings'][key] += unaffected_earnings[key]
                            else:
                                groupby_accounts[equity_unaffected_account.id][column_group_key]['unaffected_earnings'] = unaffected_earnings

        # Retrieve the accounts to browse.
        # groupby_accounts.keys() contains all account ids affected by:
        # - the amls in the current period.
        # - the amls affecting the initial balance.
        # - the unaffected earnings allocation.
        # Note a search is done instead of a browse to preserve the table ordering.
        if groupby_accounts:
            accounts = self.env['account.account'].search([('id', 'in', list(groupby_accounts.keys())),
                                                           ('id', 'in', res_user.account_ids.ids)])
        else:
            accounts = []

        return [(account, groupby_accounts[account.id]) for account in accounts]
