# * coding: utf8 *


from odoo import models, fields, api, _
from odoo.tools import float_is_zero
from datetime import timedelta


class AccountPartnerLedger(models.AbstractModel):
    _inherit = 'account.partner.ledger.report.handler'

    filter_salesperson = True

    @api.model
    def _get_options_domain(self, options, date_scope):
        domain = super(AccountPartnerLedger, self)._get_options_domain(options, date_scope)
        if options.get('salesperson') and options.get('salespersons'):
            salespersons = [int(salesperson) for salesperson in options['salespersons']]
            domain.append(('invoice_user_id', 'in', salespersons))
        return domain
