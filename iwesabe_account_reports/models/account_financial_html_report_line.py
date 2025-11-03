# * coding: utf8 *
##############################################################################
#
#    Global Creative Concepts Tech Co Ltd.
#    Copyright (C) 2018TODAY iWesabe (<http://www.iwesabe.com>).
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _
from odoo.tools import ustr, float_is_zero
import ast
from odoo.tools.safe_eval import safe_eval


# class ReportAccountFinancialReport(models.Model):
#     _inherit = "account.financial.html.report"

#     filter_salesperson = True

#     @api.model
#     def _get_options_domain(self, options):
#         domain = super(ReportAccountFinancialReport,
#                        self)._get_options_domain(options)
#         if options.get('salesperson') and options.get('salespersons'):
#             salespersons = [int(salesperson) for salesperson in options['salespersons']]
#             domain.append(('invoice_user_id', 'in', salespersons))
#         return domain
