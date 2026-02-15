import logging
from datetime import datetime, time

import pytz
from odoo import http
from odoo.http import request

from odoo.addons.muk_rest import core
from odoo.addons.muk_rest.tools.http import build_route

_logger = logging.getLogger(__name__)


class PtArchApiController(http.Controller):

    @core.http.rest_route(
        routes=build_route('/pt_arch_api/invoices'),
        methods=['GET'],
        protected=True,
        docs=dict(
            tags=['Custom'],
            summary='Get posted customer invoices',
            description='Returns all posted customer invoices with line details and sales info. Use `date_from` and `date_to` query parameters in DD/MM/YYYY (Saudi Arabia - Asia/Riyadh) format to filter by invoice date.',
            responses={
                '200': {
                    'description': 'Invoices List',
                    'content': {
                        'application/json': {
                            'schema': {'type': 'array'},
                        }
                    }
                }
            },
            parameters=[
                {
                    'name': 'date_from',
                    'in': 'query',
                    'description': 'Start date (inclusive) in DD/MM/YYYY or YYYY-MM-DD (interpreted as Asia/Riyadh)',
                    'schema': {'type': 'string'},
                    'example': '01/02/2026'
                },
                {
                    'name': 'date_to',
                    'in': 'query',
                    'description': 'End date (inclusive) in DD/MM/YYYY or YYYY-MM-DD (interpreted as Asia/Riyadh)',
                    'schema': {'type': 'string'},
                    'example': '28/02/2026'
                }
            ],
        ),
    )
    def invoices(self, **kw):
        Invoice = request.env['account.move']
        try:
            domain = [
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('state', '=', 'posted'),
            ]
            # Date filtering: accept DD/MM/YYYY (Saudi/Riyadh) or YYYY-MM-DD
            def _parse_saudi_date(s):
                if not s:
                    return None
                for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
                    try:
                        dt = datetime.strptime(s, fmt)
                        # Interpret as Asia/Riyadh local date
                        tz = pytz.timezone('Asia/Riyadh')
                        localized = tz.localize(datetime.combine(dt.date(), time.min))
                        return localized.date()
                    except Exception:
                        continue
                raise ValueError('Invalid date format: {}'.format(s))

            date_from = None
            date_to = None
            if kw.get('date_from'):
                date_from = _parse_saudi_date(kw.get('date_from'))
            if kw.get('date_to'):
                date_to = _parse_saudi_date(kw.get('date_to'))
            if date_from:
                domain.append(('invoice_date', '>=', str(date_from)))
            if date_to:
                domain.append(('invoice_date', '<=', str(date_to)))
            invoices = Invoice.search(domain)
            result = []
            for inv in invoices:
                # Resolve sale order if available
                sale_order = False
                sale_orders = inv.invoice_line_ids.mapped('sale_line_ids.order_id')
                if sale_orders:
                    sale_order = sale_orders[0]
                elif inv.invoice_origin:
                    sale_order = request.env['sale.order'].search([('name', '=', inv.invoice_origin)], limit=1)

                sales_team = sale_order.team_id.name if sale_order and sale_order.team_id else None
                sales_person = sale_order.user_id.name if sale_order and sale_order.user_id else None

                lines = []
                for line in inv.invoice_line_ids:
                    tax_names = line.tax_ids.mapped('name')
                    product_name = line.product_id.display_name or line.name
                    qty = float(line.quantity or 0.0)
                    price_unit = float(line.price_unit or 0.0)
                    line_total = float(getattr(line, 'price_subtotal', 0.0) or 0.0)
                    lines.append({
                        'product_name': product_name,
                        'quantity': qty,
                        'price_unit': price_unit,
                        'line_total': line_total,
                        'line_taxes': list(tax_names),
                    })

                result.append({
                    'invoice_id': inv.id,
                    'customer_name': inv.partner_id.name,
                    'invoice_date': str(inv.invoice_date) if inv.invoice_date else None,
                    'products': lines,
                    'invoice_total': float(inv.amount_total or 0.0),
                    'invoice_total_tax': float(inv.amount_tax or 0.0),
                    'sales_team': sales_team,
                    'sales_person': sales_person,
                })

            return request.make_json_response(result)

        except Exception as e:
            _logger.exception('Error building invoices response')
            return request.make_json_response({'error': str(e)}, status=500)
