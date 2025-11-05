from datetime import datetime, timedelta

from babel.dates import format_datetime, format_date
from odoo import models, api, _, fields
from odoo.release import version
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools.misc import formatLang, format_date as odoo_format_date, get_lang
import random

class AccountMoveInherit(models.Model):
    _inherit = 'account.journal'

    def get_line_graph_datas(self):
        """Computes the data used to display the graph for bank and cash journals in the accounting dashboard"""
        currency = self.currency_id or self.company_id.currency_id

        def build_graph_data(date, amount):
            #display date in locale format
            name = format_date(date, 'd LLLL Y', locale=locale)
            short_name = format_date(date, 'd MMM', locale=locale)
            return {'x':short_name,'y': amount, 'name':name}

        self.ensure_one()
        BankStatement = self.env['account.bank.statement']
        data = []
        today = datetime.today()
        last_month = today + timedelta(days=-30)
        locale = get_lang(self.env).code

        #starting point of the graph is the last statement
        last_stmt = self._get_last_bank_statement(domain=[('state', 'in', ['posted', 'confirm'])])

        last_balance = last_stmt and last_stmt.balance_end_real or 0
        data.append(build_graph_data(today, last_balance))

        #then we subtract the total amount of bank statement lines per day to get the previous points
        #(graph is drawn backward)
        date = today
        amount = last_balance
        query = '''
            SELECT move.date, sum(st_line.amount) as amount
            FROM account_bank_statement_line st_line
            JOIN account_move move ON move.id = st_line.move_id
            WHERE move.journal_id = %s
            AND move.date > %s
            AND move.date <= %s
            GROUP BY move.date
            ORDER BY move.date desc
        '''
        self.env.cr.execute(query, (self.id, last_month, today))
        query_result = self.env.cr.dictfetchall()
        for val in query_result:
            if val['amount']:
                date = val['date']
                if date != today.strftime(DF):  # make sure the last point in the graph is today
                    data[:0] = [build_graph_data(date, amount)]
                amount = currency.round(amount - val['amount'])

        # make sure the graph starts 1 month ago
        if date.strftime(DF) != last_month.strftime(DF):
            data[:0] = [build_graph_data(last_month, amount)]

        [graph_title, graph_key] = self._graph_title_and_key()
        color = '#875A7B' if 'e' in version else '#7c7bad'

        is_sample_data = not last_stmt and len(query_result) == 0
        if is_sample_data:
            data = []
            for i in range(30, 0, -5):
                current_date = today + timedelta(days=-i)
                data.append(build_graph_data(current_date, random.randint(-5, 15)))

        return [{'values': data, 'title': graph_title, 'key': graph_key, 'area': True, 'color': color, 'is_sample_data': is_sample_data}]
