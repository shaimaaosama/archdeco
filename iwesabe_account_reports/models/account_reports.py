# * coding: utf8 *


from odoo import models, fields, api, _


class AccountReport(models.Model):
    _inherit = 'account.report'

    filter_salesperson = fields.Boolean(
        string="Sales Persons",
        compute=lambda x: x._compute_report_option_filter('filter_salesperson'), readonly=False, store=True, depends=['root_report_id'],
    )

    @api.model
    def _init_options_salesperson(self, options, previous_options=None):
        query = "UPDATE account_move_line SET invoice_user_id=(SELECT invoice_user_id from account_move where id=account_move_line.move_id) WHERE account_move_line.invoice_user_id is NULL;"
        self.env.cr.execute(query)
        options['salesperson'] = True
        res_salesperson_obj = self.env['res.users']
        options['salespersons'] = previous_options and previous_options.get('salespersons') or [
        ]
        
        invoice_user_ids = [int(salesperson) for salesperson in options['salespersons']]
        selected_invoice_user_ids = invoice_user_ids and res_salesperson_obj.browse(
            invoice_user_ids) or res_salesperson_obj
        options['selected_invoice_user_ids'] = selected_invoice_user_ids.mapped('name')

    def _set_context(self, options):
        ctx = super(AccountReport, self)._set_context(options)
        if options.get('salespersons'):
            ctx['invoice_user_ids'] = self.env['res.users'].browse(
                [int(salesperson) for salesperson in options['salespersons']]).ids
        return ctx

    def get_report_informations(self, options):
        options = self._get_options(options)
        if options.get('salesperson'):
            options['selected_invoice_user_ids'] = [self.env['res.users'].browse(
                int(salesperson)).name for salesperson in options['salespersons']]
        return super(AccountReport, self).get_report_informations(options)

    @api.model
    def _get_options_domain(self, options, date_scope):
        domain = super(AccountReport, self)._get_options_domain(options, date_scope)
        if options.get('salesperson') and options.get('salespersons'):
            salespersons = [int(salesperson) for salesperson in options['salespersons']]
            domain.append(('invoice_user_id', 'in', salespersons))
        return domain