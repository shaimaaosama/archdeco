# -*- coding: utf-8 -*-

import base64
import io
from collections import defaultdict, deque
from datetime import datetime, time

import pytz
import xlsxwriter

from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero


class InventoryAgingDashboard(models.TransientModel):
    _name = 'inventory.aging.dashboard'
    _description = 'Inventory Aging Dashboard'

    _brand_field_candidates = ('product_brand_id', 'custom_brand_id', 'brand_id', 'x_brand_id', 'x_product_brand_id')

    @api.model
    def _int_ids(self, values):
        if not values:
            return []
        if not isinstance(values, (list, tuple)):
            values = [values]
        result = []
        for value in values:
            try:
                value = int(value)
                if value:
                    result.append(value)
            except (TypeError, ValueError):
                pass
        return result

    @api.model
    def _get_view_mode(self, filters=None):
        value = (filters or {}).get('view_mode') or 'detailed'
        return value if value in ('detailed', 'summary') else 'detailed'

    @api.model
    def _get_aging_period_days(self, filters=None):
        try:
            value = int(str((filters or {}).get('aging_period_days') or 30).strip())
        except (TypeError, ValueError):
            value = 30
        return value if value > 0 else 30

    @api.model
    def _get_last_period_days(self, days):
        return max(int(days or 30), 1) * 5

    @api.model
    def _get_aged_threshold_days(self, days):
        return int(self._get_last_period_days(days) / 2)

    @api.model
    def _get_aging_period_labels(self, days):
        days = max(int(days or 30), 1)
        return ['0-%s' % days, '%s-%s' % (days + 1, days * 2), '%s-%s' % (days * 2 + 1, days * 3), '%s-%s' % (days * 3 + 1, days * 4), '%s-%s' % (days * 4 + 1, days * 5), '>%s' % (days * 5)]

    @api.model
    def _get_brand_field(self):
        model = self.env['product.template']
        for name in self._brand_field_candidates:
            field = model._fields.get(name)
            if field and field.type == 'many2one':
                return name, field
        return False, False

    @api.model
    def _storable_product_domain(self, company_ids=None):
        company_ids = company_ids or self.env.companies.ids
        domain = [('product_tmpl_id.company_id', 'in', [False] + company_ids)]
        model = self.env['product.template']
        if 'is_storable' in model._fields:
            domain.append(('product_tmpl_id.is_storable', '=', True))
        elif 'detailed_type' in model._fields:
            domain.append(('product_tmpl_id.detailed_type', '=', 'product'))
        else:
            domain.append(('product_tmpl_id.type', '=', 'product'))
        return domain

    @api.model
    def _get_cutoff_datetime(self, aging_date):
        tz = pytz.timezone(self.env.user.tz or 'UTC')
        return tz.localize(datetime.combine(aging_date, time.max)).astimezone(pytz.UTC).replace(tzinfo=None)

    @api.model
    def _get_start_datetime(self, start_date):
        tz = pytz.timezone(self.env.user.tz or 'UTC')
        return tz.localize(datetime.combine(start_date, time.min)).astimezone(pytz.UTC).replace(tzinfo=None)

    @api.model
    def _get_turnover_period_start(self, aging_date):
        return aging_date.replace(month=1, day=1)

    @api.model
    def search_filter_options(self, filter_name, search_term='', selected_values=None):
        selected_values = selected_values or []
        search_term = (search_term or '').strip()
        if filter_name == 'warehouse':
            domain = [('company_id', 'in', self.env.companies.ids)]
            if search_term:
                domain.append(('name', 'ilike', search_term))
            records = self.env['stock.warehouse'].search(domain, order='company_id, name', limit=80)
            records |= self.env['stock.warehouse'].browse(self._int_ids(selected_values)).exists()
            return [{'value': str(r.id), 'label': r.display_name} for r in records.sorted(lambda r: r.display_name or '')]
        if filter_name == 'category':
            domain = [('complete_name', 'ilike', search_term)] if search_term else []
            records = self.env['product.category'].search(domain, order='complete_name', limit=80)
            records |= self.env['product.category'].browse(self._int_ids(selected_values)).exists()
            return [{'value': str(r.id), 'label': r.complete_name or r.display_name} for r in records.sorted(lambda r: r.complete_name or r.display_name or '')]
        if filter_name == 'brand':
            name, field = self._get_brand_field()
            if not name:
                return []
            model = self.env[field.comodel_name]
            domain = [('name', 'ilike', search_term)] if search_term else []
            records = model.search(domain, order='name', limit=80)
            records |= model.browse(self._int_ids(selected_values)).exists()
            return [{'value': str(r.id), 'label': r.display_name} for r in records.sorted(lambda r: r.display_name or '')]
        if filter_name == 'product':
            domain = self._storable_product_domain()
            if search_term:
                domain += ['|', ('default_code', 'ilike', search_term), ('name', 'ilike', search_term)]
            records = self.env['product.product'].search(domain, order='default_code, name', limit=100)
            records |= self.env['product.product'].browse(self._int_ids(selected_values)).exists()
            return [{'value': str(r.id), 'label': '[%s] %s' % (r.default_code, r.name) if r.default_code else r.name} for r in records.sorted(lambda r: (r.default_code or '', r.name or ''))]
        return []

    @api.model
    def _get_products(self, filters, company_ids):
        domain = self._storable_product_domain(company_ids)
        category_ids = self._int_ids(filters.get('category_ids'))
        product_ids = self._int_ids(filters.get('product_ids'))
        brand_ids = self._int_ids(filters.get('brand_values'))
        if category_ids:
            domain.append(('categ_id', 'child_of', category_ids))
        if product_ids:
            domain.append(('id', 'in', product_ids))
        brand_name, brand_field = self._get_brand_field()
        if brand_ids and brand_name and brand_field:
            domain.append(('product_tmpl_id.%s' % brand_name, 'in', brand_ids))
        return self.env['product.product'].search(domain)

    @api.model
    def _get_internal_locations(self, warehouses, company_ids):
        locations = self.env['stock.location'].search([('usage', '=', 'internal'), '|', ('company_id', '=', False), ('company_id', 'in', company_ids)])
        roots = [(w, w.view_location_id.parent_path or '') for w in warehouses]
        roots.sort(key=lambda x: len(x[1]), reverse=True)
        location_warehouse = {}
        for location in locations:
            path = location.parent_path or ''
            for warehouse, root in roots:
                if root and path.startswith(root):
                    location_warehouse[location.id] = warehouse.id
                    break
        return locations, location_warehouse

    @api.model
    def _area_key(self, location_id, company_id, location_warehouse):
        warehouse_id = location_warehouse.get(location_id)
        if warehouse_id:
            return ('warehouse', warehouse_id, company_id or self.env.company.id)
        return ('location', location_id, company_id or self.env.company.id)

    @api.model
    def _area_name(self, area_key):
        if area_key[0] == 'warehouse':
            record = self.env['stock.warehouse'].browse(area_key[1]).exists()
            return record.display_name if record else 'Warehouse'
        record = self.env['stock.location'].browse(area_key[1]).exists()
        return (record.complete_name or record.display_name or record.name) if record else 'Internal Location'

    @api.model
    def _current_internal_qty(self, products, internal_location_ids, location_warehouse):
        result = defaultdict(float)
        if not products or not internal_location_ids:
            return result
        self.env.cr.execute('''
            SELECT sq.product_id, sq.location_id, COALESCE(sq.company_id, sl.company_id), SUM(sq.quantity)
              FROM stock_quant sq
              JOIN stock_location sl ON sl.id = sq.location_id
             WHERE sq.product_id = ANY(%s)
               AND sq.location_id = ANY(%s)
               AND sl.usage = 'internal'
             GROUP BY sq.product_id, sq.location_id, COALESCE(sq.company_id, sl.company_id)
            HAVING ABS(SUM(sq.quantity)) > 0.00000001
        ''', [products.ids, internal_location_ids])
        for product_id, location_id, company_id, qty in self.env.cr.fetchall():
            result[(product_id, self._area_key(location_id, company_id, location_warehouse))] += float(qty or 0.0)
        return result

    @api.model
    def _historical_internal_qty(self, company_ids, product_ids, internal_location_ids, cutoff, location_warehouse):
        result = defaultdict(float)
        if not product_ids or not internal_location_ids:
            return result
        self.env.cr.execute('''
            SELECT x.product_id, x.location_id, x.company_id, SUM(x.qty)
              FROM (
                    SELECT sml.product_id, sml.location_dest_id location_id, sm.company_id,
                           (sml.quantity / NULLIF(mu.factor, 0.0)) * pu.factor qty
                      FROM stock_move_line sml
                      JOIN stock_move sm ON sm.id = sml.move_id
                      JOIN product_product pp ON pp.id = sml.product_id
                      JOIN product_template pt ON pt.id = pp.product_tmpl_id
                      JOIN uom_uom mu ON mu.id = sml.product_uom_id
                      JOIN uom_uom pu ON pu.id = pt.uom_id
                     WHERE sm.state = 'done' AND sm.date <= %s AND sm.company_id = ANY(%s)
                       AND sml.product_id = ANY(%s) AND sml.location_dest_id = ANY(%s) AND sml.quantity != 0
                    UNION ALL
                    SELECT sml.product_id, sml.location_id location_id, sm.company_id,
                           -((sml.quantity / NULLIF(mu.factor, 0.0)) * pu.factor) qty
                      FROM stock_move_line sml
                      JOIN stock_move sm ON sm.id = sml.move_id
                      JOIN product_product pp ON pp.id = sml.product_id
                      JOIN product_template pt ON pt.id = pp.product_tmpl_id
                      JOIN uom_uom mu ON mu.id = sml.product_uom_id
                      JOIN uom_uom pu ON pu.id = pt.uom_id
                     WHERE sm.state = 'done' AND sm.date <= %s AND sm.company_id = ANY(%s)
                       AND sml.product_id = ANY(%s) AND sml.location_id = ANY(%s) AND sml.quantity != 0
                   ) x
             GROUP BY x.product_id, x.location_id, x.company_id
            HAVING ABS(SUM(x.qty)) > 0.00000001
        ''', [cutoff, company_ids, product_ids, internal_location_ids, cutoff, company_ids, product_ids, internal_location_ids])
        for product_id, location_id, company_id, qty in self.env.cr.fetchall():
            result[(product_id, self._area_key(location_id, company_id, location_warehouse))] += float(qty or 0.0)
        return result

    @api.model
    def _get_internal_qty(self, products, aging_date, company_ids, internal_location_ids, cutoff, location_warehouse):
        if aging_date == fields.Date.context_today(self):
            return self._current_internal_qty(products, internal_location_ids, location_warehouse)
        return self._historical_internal_qty(company_ids, products.ids, internal_location_ids, cutoff, location_warehouse)

    @api.model
    def _get_move_rows(self, company_ids, product_ids, internal_location_ids, cutoff):
        if not product_ids or not internal_location_ids:
            return []
        self.env.cr.execute('''
            SELECT sml.id, sml.product_id, sml.location_id, sml.location_dest_id,
                   (sml.quantity / NULLIF(mu.factor, 0.0)) * pu.factor qty, sm.date, sm.company_id
              FROM stock_move_line sml
              JOIN stock_move sm ON sm.id = sml.move_id
              JOIN product_product pp ON pp.id = sml.product_id
              JOIN product_template pt ON pt.id = pp.product_tmpl_id
              JOIN uom_uom mu ON mu.id = sml.product_uom_id
              JOIN uom_uom pu ON pu.id = pt.uom_id
             WHERE sm.state = 'done' AND sm.date <= %s AND sm.company_id = ANY(%s)
               AND sml.product_id = ANY(%s)
               AND (sml.location_id = ANY(%s) OR sml.location_dest_id = ANY(%s))
               AND sml.quantity != 0
             ORDER BY sm.date, sml.id
        ''', [cutoff, company_ids, product_ids, internal_location_ids, internal_location_ids])
        return self.env.cr.fetchall()

    @api.model
    def _simulate_fifo(self, move_rows, internal_location_ids, location_warehouse):
        internal_location_ids = set(internal_location_ids)
        layers = defaultdict(deque)
        shortage = defaultdict(float)
        last_receipt = {}
        last_issue = {}

        def consume(key, qty, move_date):
            pieces = []
            while qty > 1e-12 and layers[key]:
                origin, available = layers[key][0]
                taken = min(available, qty)
                pieces.append([origin, taken])
                available -= taken
                qty -= taken
                if available <= 1e-12:
                    layers[key].popleft()
                else:
                    layers[key][0][1] = available
            if qty > 1e-12:
                shortage[key] += qty
                pieces.append([move_date, qty])
            return pieces

        def add(key, pieces):
            for origin, qty in pieces:
                if shortage[key] > 0:
                    offset = min(shortage[key], qty)
                    shortage[key] -= offset
                    qty -= offset
                if qty > 1e-12:
                    layers[key].append([origin, qty])

        for _id, product_id, source_id, dest_id, qty, move_dt, company_id in move_rows:
            qty = float(qty or 0.0)
            if qty <= 0:
                continue
            move_date = fields.Datetime.to_datetime(move_dt).date()
            source_internal = source_id in internal_location_ids
            dest_internal = dest_id in internal_location_ids
            source_key = (product_id, source_id, company_id)
            dest_key = (product_id, dest_id, company_id)
            source_area = self._area_key(source_id, company_id, location_warehouse) if source_internal else False
            dest_area = self._area_key(dest_id, company_id, location_warehouse) if dest_internal else False
            if source_area != dest_area:
                if source_internal:
                    last_issue[(product_id, source_area)] = move_date
                if dest_internal:
                    last_receipt[(product_id, dest_area)] = move_date
            pieces = consume(source_key, qty, move_date) if source_internal else [[move_date, qty]]
            if dest_internal:
                add(dest_key, pieces)

        area_layers = defaultdict(list)
        for (product_id, location_id, company_id), queue in layers.items():
            area_layers[(product_id, self._area_key(location_id, company_id, location_warehouse))].extend(list(queue))
        return {'area_layers': area_layers, 'last_receipt': last_receipt, 'last_issue': last_issue}

    @api.model
    def _valuation_totals(self, products, companies, cutoff):
        result = {}
        if not products:
            return result
        self.env.cr.execute('''
            SELECT product_id, company_id, SUM(quantity), SUM(value)
              FROM stock_valuation_layer
             WHERE product_id = ANY(%s) AND company_id = ANY(%s) AND create_date <= %s
             GROUP BY product_id, company_id
        ''', [products.ids, companies.ids, cutoff])
        for product_id, company_id, qty, value in self.env.cr.fetchall():
            result[(product_id, company_id)] = {'quantity': float(qty or 0.0), 'value': float(value or 0.0)}
        return result

    @api.model
    def _opening_valuation(self, products, companies, period_start):
        result = {}
        if not products:
            return result
        start = self._get_start_datetime(period_start)
        self.env.cr.execute('''
            SELECT product_id, company_id, SUM(quantity), SUM(value)
              FROM stock_valuation_layer
             WHERE product_id = ANY(%s) AND company_id = ANY(%s) AND create_date < %s
             GROUP BY product_id, company_id
        ''', [products.ids, companies.ids, start])
        for product_id, company_id, qty, value in self.env.cr.fetchall():
            result[(product_id, company_id)] = {'quantity': float(qty or 0.0), 'value': float(value or 0.0)}
        return result

    @api.model
    def _cogs_totals(self, products, companies, period_start, cutoff):
        result = defaultdict(float)
        if not products:
            return result
        start = self._get_start_datetime(period_start)
        self.env.cr.execute('''
            SELECT svl.product_id, svl.company_id,
                   SUM(CASE WHEN src.usage = 'internal' AND dst.usage = 'customer' THEN -svl.value
                            WHEN src.usage = 'customer' AND dst.usage = 'internal' THEN -svl.value ELSE 0 END)
              FROM stock_valuation_layer svl
              JOIN stock_move sm ON sm.id = svl.stock_move_id
              JOIN stock_location src ON src.id = sm.location_id
              JOIN stock_location dst ON dst.id = sm.location_dest_id
             WHERE svl.product_id = ANY(%s) AND svl.company_id = ANY(%s)
               AND sm.state = 'done' AND sm.date >= %s AND sm.date <= %s
             GROUP BY svl.product_id, svl.company_id
        ''', [products.ids, companies.ids, start, cutoff])
        for product_id, company_id, value in self.env.cr.fetchall():
            result[(product_id, company_id)] = float(value or 0.0)
        return result

    @api.model
    def _build_detail_rows(self, products, report_warehouses, include_unmapped_internal, aging_date, aging_days, qty_totals, simulation, valuations):
        product_map = {p.id: p for p in products}
        selected_warehouse_ids = set(report_warehouses.ids)
        last_period = self._get_last_period_days(aging_days)
        aged_threshold = self._get_aged_threshold_days(aging_days)
        brand_name, _field = self._get_brand_field()
        rows = []

        for (product_id, area_key), current_qty in qty_totals.items():
            if area_key[0] == 'warehouse' and area_key[1] not in selected_warehouse_ids:
                continue
            if area_key[0] == 'location' and not include_unmapped_internal:
                continue
            product = product_map.get(product_id)
            if not product:
                continue
            current_qty = float(current_qty or 0.0)
            if float_is_zero(current_qty, precision_rounding=product.uom_id.rounding or 0.01):
                continue

            company_id = area_key[2]
            valuation = valuations.get((product_id, company_id), {})
            valuation_qty = float(valuation.get('quantity') or 0.0)
            valuation_value = float(valuation.get('value') or 0.0)
            unit_cost = valuation_value / valuation_qty if not float_is_zero(valuation_qty, precision_rounding=1e-8) else 0.0
            current_value = current_qty * unit_cost

            layers = simulation['area_layers'].get((product_id, area_key), [])
            layer_qty = sum(float(x[1] or 0.0) for x in layers)
            weighted_days = sum(float(qty or 0.0) * max((aging_date - origin).days, 0) for origin, qty in layers)
            weighted_age = weighted_days / layer_qty if layer_qty else 0.0
            oldest = min([origin for origin, qty in layers if qty > 0], default=False)

            buckets = {'0_30': 0.0, '31_60': 0.0, '61_90': 0.0, '91_180': 0.0, '181_365': 0.0, 'over_365': 0.0}
            if current_qty > 0:
                if weighted_age <= aging_days:
                    buckets['0_30'] = current_qty
                elif weighted_age <= aging_days * 2:
                    buckets['31_60'] = current_qty
                elif weighted_age <= aging_days * 3:
                    buckets['61_90'] = current_qty
                elif weighted_age <= aging_days * 4:
                    buckets['91_180'] = current_qty
                elif weighted_age <= aging_days * 5:
                    buckets['181_365'] = current_qty
                else:
                    buckets['over_365'] = current_qty

            values = {key: qty * unit_cost for key, qty in buckets.items()}
            last_receipt = simulation['last_receipt'].get((product_id, area_key))
            last_issue = simulation['last_issue'].get((product_id, area_key))
            days_receipt = (aging_date - last_receipt).days if last_receipt else False
            days_issue = (aging_date - last_issue).days if last_issue else False
            no_movement = bool(days_receipt is not False and days_issue is not False and days_receipt > last_period and days_issue > last_period)
            aged_qty = current_qty if current_qty > 0 and weighted_age > aged_threshold else 0.0
            aged_value = current_value if current_value > 0 and weighted_age > aged_threshold else 0.0
            aged_pct_qty = aged_qty / current_qty if current_qty > 0 else 0.0
            aged_pct_value = aged_value / current_value if current_value > 0 else 0.0
            negative = current_qty < 0
            risk = 'CRITICAL' if negative else 'HIGH' if no_movement else 'MEDIUM' if aged_pct_qty >= .5 or aged_pct_value >= .5 else 'LOW'
            brand = product.product_tmpl_id[brand_name] if brand_name else False

            rows.append({
                'key': '%s:%s:%s:%s' % (product_id, area_key[0], area_key[1], company_id), 'product_id': product_id, 'company_id': company_id,
                'warehouse_id': area_key[1] if area_key[0] == 'warehouse' else False, 'location_id': area_key[1] if area_key[0] == 'location' else False,
                'internal_reference': product.default_code or '', 'product_name': product.with_context(display_default_code=False).display_name,
                'brand': brand.display_name if brand else '', 'category': product.categ_id.complete_name or product.categ_id.display_name or '', 'uom': product.uom_id.display_name or '', 'warehouse': self._area_name(area_key),
                'current_qty': current_qty, 'current_value': current_value, 'closing_avg_cost': unit_cost, 'oldest_stock_date': oldest.isoformat() if oldest else '', 'weighted_avg_age': weighted_age,
                'qty_0_30': buckets['0_30'], 'value_0_30': values['0_30'], 'qty_31_60': buckets['31_60'], 'value_31_60': values['31_60'], 'qty_61_90': buckets['61_90'], 'value_61_90': values['61_90'],
                'qty_91_180': buckets['91_180'], 'value_91_180': values['91_180'], 'qty_181_365': buckets['181_365'], 'value_181_365': values['181_365'], 'qty_over_365': buckets['over_365'], 'value_over_365': values['over_365'],
                'last_receipt_date': last_receipt.isoformat() if last_receipt else '', 'last_issue_date': last_issue.isoformat() if last_issue else '', 'days_since_receipt': days_receipt if days_receipt is not False else '', 'days_since_issue': days_issue if days_issue is not False else '',
                'aged_qty_180': aged_qty, 'aged_value_180': aged_value, 'aged_percent_qty': aged_pct_qty, 'aged_percent_value': aged_pct_value,
                'qty_reconciliation': current_qty - sum(buckets.values()), 'value_reconciliation': current_value - sum(values.values()), 'negative_stock_flag': 'YES' if negative else 'NO', 'no_movement_365': 'YES' if no_movement else 'NO', 'aging_risk_level': risk,
            })
        return rows

    @api.model
    def _build_summary_rows(self, detail_rows, aging_date, aging_days, valuations, opening, cogs, exact_valuation=True):
        grouped = defaultdict(list)
        for row in detail_rows:
            grouped[row['product_id']].append(row)
        last_period = self._get_last_period_days(aging_days)
        result = []
        for product_id, rows in grouped.items():
            first = rows[0]
            company_ids = {r['company_id'] for r in rows if r.get('company_id')}
            internal_qty = sum(float(r.get('current_qty') or 0.0) for r in rows)
            internal_value = sum(float(r.get('current_value') or 0.0) for r in rows)
            valuation_qty = sum(float(valuations.get((product_id, c), {}).get('quantity') or 0.0) for c in company_ids)
            valuation_value = sum(float(valuations.get((product_id, c), {}).get('value') or 0.0) for c in company_ids)
            current_qty = valuation_qty if exact_valuation else internal_qty
            current_value = valuation_value if exact_valuation else internal_value
            avg_cost = current_value / current_qty if not float_is_zero(current_qty, precision_rounding=1e-8) else 0.0

            def s(key):
                return sum(float(r.get(key) or 0.0) for r in rows)

            aged_qty, aged_value = s('aged_qty_180'), s('aged_value_180')
            aged_pct_qty = aged_qty / current_qty if current_qty > 0 else 0.0
            aged_pct_value = aged_value / current_value if current_value > 0 else 0.0
            pos_qty = sum(max(float(r.get('current_qty') or 0.0), 0.0) for r in rows)
            weighted_age = sum(float(r.get('weighted_avg_age') or 0.0) * max(float(r.get('current_qty') or 0.0), 0.0) for r in rows) / pos_qty if pos_qty else 0.0
            oldest = min([r['oldest_stock_date'] for r in rows if r.get('oldest_stock_date')], default='')
            receipts = [r['last_receipt_date'] for r in rows if r.get('last_receipt_date')]
            issues = [r['last_issue_date'] for r in rows if r.get('last_issue_date')]
            latest_receipt = max(receipts) if receipts else False
            latest_issue = max(issues) if issues else False
            dr = (aging_date - fields.Date.to_date(latest_receipt)).days if latest_receipt else False
            di = (aging_date - fields.Date.to_date(latest_issue)).days if latest_issue else False
            no_movement = bool(dr is not False and di is not False and dr > last_period and di > last_period)
            negative = any(r.get('negative_stock_flag') == 'YES' for r in rows)
            risk = 'CRITICAL' if negative else 'HIGH' if no_movement else 'MEDIUM' if aged_pct_qty >= .5 or aged_pct_value >= .5 else 'LOW'
            opening_value = sum(float(opening.get((product_id, c), {}).get('value') or 0.0) for c in company_ids)
            cogs_value = sum(float(cogs.get((product_id, c), 0.0) or 0.0) for c in company_ids)
            average_value = (opening_value + current_value) / 2.0
            turnover = cogs_value / average_value if average_value > 0 else 0.0
            dio = 365.0 / turnover if turnover > 0 else 0.0

            result.append({
                'key': 'summary:%s' % product_id, 'product_id': product_id, 'company_id': False, 'warehouse_id': False, 'location_id': False,
                'internal_reference': first.get('internal_reference') or '', 'product_name': first.get('product_name') or '', 'brand': first.get('brand') or '', 'category': first.get('category') or '', 'uom': first.get('uom') or '', 'warehouse': 'Consolidated',
                'current_qty': current_qty, 'current_value': current_value, 'closing_avg_cost': avg_cost,
                'qty_0_30': s('qty_0_30'), 'value_0_30': s('value_0_30'), 'qty_31_60': s('qty_31_60'), 'value_31_60': s('value_31_60'), 'qty_61_90': s('qty_61_90'), 'value_61_90': s('value_61_90'),
                'qty_91_180': s('qty_91_180'), 'value_91_180': s('value_91_180'), 'qty_181_365': s('qty_181_365'), 'value_181_365': s('value_181_365'), 'qty_over_365': s('qty_over_365'), 'value_over_365': s('value_over_365'),
                'oldest_stock_date': oldest, 'weighted_avg_age': weighted_age, 'aged_qty_180': aged_qty, 'aged_value_180': aged_value, 'aged_percent_qty': aged_pct_qty, 'aged_percent_value': aged_pct_value,
                'warehouse_qty_check': internal_qty - valuation_qty, 'warehouse_value_check': internal_value - valuation_value, 'no_movement_365': 'YES' if no_movement else 'NO', 'aging_risk_level': risk,
                'opening_inventory_value': opening_value, 'cogs_selected_period': cogs_value, 'average_inventory_value': average_value, 'inventory_turnover_ratio': turnover, 'dio_days': dio,
                'negative_stock_flag': 'YES' if negative else 'NO',
            })
        return result

    @api.model
    def _apply_filters(self, rows, filters):
        negative = filters.get('negative_stock') or 'all'
        no_movement = filters.get('no_movement') or 'all'
        risks = set(filters.get('risk_levels') or [])
        search = (filters.get('search_text') or '').strip().lower()
        result = []
        for row in rows:
            if negative == 'yes' and row.get('negative_stock_flag') != 'YES':
                continue
            if negative == 'no' and row.get('negative_stock_flag') != 'NO':
                continue
            if no_movement == 'yes' and row.get('no_movement_365') != 'YES':
                continue
            if no_movement == 'no' and row.get('no_movement_365') != 'NO':
                continue
            if risks and row.get('aging_risk_level') not in risks:
                continue
            if search:
                value = ' '.join(str(row.get(k) or '') for k in ('internal_reference', 'product_name', 'brand', 'category', 'warehouse', 'aging_risk_level')).lower()
                if search not in value:
                    continue
            result.append(row)
        return result

    @api.model
    def _get_report_data(self, filters=None):
        filters = filters or {}
        view_mode = self._get_view_mode(filters)
        aging_days = self._get_aging_period_days(filters)
        aging_date = fields.Date.to_date(filters.get('aging_date')) or fields.Date.context_today(self)
        companies = self.env.companies
        company_ids = companies.ids
        warehouses = self.env['stock.warehouse'].search([('company_id', 'in', company_ids)])
        warehouse_ids = self._int_ids(filters.get('warehouse_ids'))
        report_warehouses = warehouses.filtered(lambda w: w.id in warehouse_ids) if warehouse_ids else warehouses
        products = self._get_products(filters, company_ids)
        empty = {'rows': [], 'aging_date': aging_date, 'aging_period_days': aging_days, 'aging_period_labels': self._get_aging_period_labels(aging_days), 'view_mode': view_mode}
        if not products:
            return empty

        cutoff = self._get_cutoff_datetime(aging_date)
        internal_locations, location_warehouse = self._get_internal_locations(warehouses, company_ids)
        if not internal_locations:
            return empty

        qty_totals = self._get_internal_qty(products, aging_date, company_ids, internal_locations.ids, cutoff, location_warehouse)
        active_ids = sorted({product_id for product_id, area in qty_totals if not float_is_zero(float(qty_totals[(product_id, area)] or 0.0), precision_rounding=1e-8)})
        if not active_ids:
            return empty

        active_products = products.filtered(lambda p: p.id in active_ids)
        move_rows = self._get_move_rows(company_ids, active_ids, internal_locations.ids, cutoff)
        simulation = self._simulate_fifo(move_rows, internal_locations.ids, location_warehouse)
        valuations = self._valuation_totals(active_products, companies, cutoff)
        detail_rows = self._build_detail_rows(active_products, report_warehouses, not warehouse_ids, aging_date, aging_days, qty_totals, simulation, valuations)

        if view_mode == 'summary':
            period_start = self._get_turnover_period_start(aging_date)
            opening = self._opening_valuation(active_products, companies, period_start)
            cogs = self._cogs_totals(active_products, companies, period_start, cutoff)
            rows = self._build_summary_rows(detail_rows, aging_date, aging_days, valuations, opening, cogs, exact_valuation=not warehouse_ids)
        else:
            rows = detail_rows

        rows = self._apply_filters(rows, filters)
        rows.sort(key=lambda r: (r.get('internal_reference') or '', r.get('product_name') or '', r.get('warehouse') or ''))
        return {'rows': rows, 'aging_date': aging_date, 'aging_period_days': aging_days, 'aging_period_labels': self._get_aging_period_labels(aging_days), 'view_mode': view_mode}

    @api.model
    def _prepare_summary(self, rows):
        summary = {'lines': len(rows), 'products': len({r['product_id'] for r in rows}), 'total_qty': 0.0, 'total_value': 0.0, 'negative_lines': 0, 'no_movement_lines': 0, 'low_risk': 0, 'medium_risk': 0, 'high_risk': 0, 'critical_risk': 0, 'bucket_0_30_value': 0.0, 'bucket_31_60_value': 0.0, 'bucket_61_90_value': 0.0, 'bucket_91_180_value': 0.0, 'bucket_181_365_value': 0.0, 'bucket_over_365_value': 0.0}
        for row in rows:
            summary['total_qty'] += float(row.get('current_qty') or 0.0)
            summary['total_value'] += float(row.get('current_value') or 0.0)
            for key in ('0_30', '31_60', '61_90', '91_180', '181_365', 'over_365'):
                summary['bucket_%s_value' % key] += float(row.get('value_%s' % key) or 0.0)
            if row.get('negative_stock_flag') == 'YES':
                summary['negative_lines'] += 1
            if row.get('no_movement_365') == 'YES':
                summary['no_movement_lines'] += 1
            risk = (row.get('aging_risk_level') or '').lower()
            if '%s_risk' % risk in summary:
                summary['%s_risk' % risk] += 1
        return summary

    @api.model
    def _column_totals(self, rows):
        keys = ('current_qty', 'current_value', 'qty_0_30', 'value_0_30', 'qty_31_60', 'value_31_60', 'qty_61_90', 'value_61_90', 'qty_91_180', 'value_91_180', 'qty_181_365', 'value_181_365', 'qty_over_365', 'value_over_365', 'aged_qty_180', 'aged_value_180', 'qty_reconciliation', 'value_reconciliation', 'warehouse_qty_check', 'warehouse_value_check', 'opening_inventory_value', 'cogs_selected_period', 'average_inventory_value')
        totals = {k: sum(float(r.get(k) or 0.0) for r in rows) for k in keys}
        average = (totals['opening_inventory_value'] + totals['current_value']) / 2.0
        turnover = totals['cogs_selected_period'] / average if average > 0 else 0.0
        totals['average_inventory_value'] = average
        totals['inventory_turnover_ratio'] = turnover
        totals['dio_days'] = 365.0 / turnover if turnover > 0 else 0.0
        return totals

    @api.model
    def get_dashboard_data(self, filters=None):
        filters = filters or {}
        report = self._get_report_data(filters)
        rows = report['rows']
        page_size = max(20, min(int(filters.get('page_size') or 100), 500))
        total_rows = len(rows)
        total_pages = max(1, (total_rows + page_size - 1) // page_size)
        page = min(max(int(filters.get('page') or 1), 1), total_pages)
        start = (page - 1) * page_size
        days = report['aging_period_days']
        return {'aging_date': report['aging_date'].isoformat(), 'aging_period_days': days, 'last_period_days': self._get_last_period_days(days), 'aged_threshold_days': self._get_aged_threshold_days(days), 'aging_period_labels': report['aging_period_labels'], 'view_mode': report['view_mode'], 'rows': rows[start:start + page_size], 'summary': self._prepare_summary(rows), 'column_totals': self._column_totals(rows), 'page': page, 'page_size': page_size, 'total_rows': total_rows, 'total_pages': total_pages}

    @api.model
    def _detailed_excel_columns(self, days):
        labels = self._get_aging_period_labels(days)
        aged = self._get_aged_threshold_days(days)
        last = self._get_last_period_days(days)
        return [('internal_reference', 'Internal Reference', 'text'), ('product_name', 'Product Name', 'text'), ('brand', 'Brand', 'text'), ('category', 'Product Category', 'text'), ('uom', 'UOM', 'text'), ('warehouse', 'Warehouse / Internal Location', 'text'), ('current_qty', 'Current Qty', 'number'), ('current_value', 'Current Value', 'amount'), ('closing_avg_cost', 'Closing Avg. Cost', 'amount'), ('oldest_stock_date', 'Oldest Stock Date', 'text'), ('weighted_avg_age', 'Weighted Avg. Age', 'number'), ('qty_0_30', labels[0] + ' Qty', 'number'), ('value_0_30', labels[0] + ' Value', 'amount'), ('qty_31_60', labels[1] + ' Qty', 'number'), ('value_31_60', labels[1] + ' Value', 'amount'), ('qty_61_90', labels[2] + ' Qty', 'number'), ('value_61_90', labels[2] + ' Value', 'amount'), ('qty_91_180', labels[3] + ' Qty', 'number'), ('value_91_180', labels[3] + ' Value', 'amount'), ('qty_181_365', labels[4] + ' Qty', 'number'), ('value_181_365', labels[4] + ' Value', 'amount'), ('qty_over_365', labels[5] + ' Qty', 'number'), ('value_over_365', labels[5] + ' Value', 'amount'), ('last_receipt_date', 'Last Receipt Date', 'text'), ('last_issue_date', 'Last Issue Date', 'text'), ('days_since_receipt', 'Days Since Receipt', 'number'), ('days_since_issue', 'Days Since Issue', 'number'), ('aged_qty_180', 'Aged Qty >%s' % aged, 'number'), ('aged_value_180', 'Aged Value >%s' % aged, 'amount'), ('aged_percent_qty', 'Aged >%s %% Qty' % aged, 'percent'), ('aged_percent_value', 'Aged >%s %% Value' % aged, 'percent'), ('qty_reconciliation', 'Qty Reconciliation', 'number'), ('value_reconciliation', 'Value Reconciliation', 'amount'), ('negative_stock_flag', 'Negative Stock', 'text'), ('no_movement_365', 'No Movement >%s' % last, 'text'), ('aging_risk_level', 'Aging Risk Level', 'text')]

    @api.model
    def _summary_excel_columns(self, days):
        labels = self._get_aging_period_labels(days)
        aged = self._get_aged_threshold_days(days)
        last = self._get_last_period_days(days)
        return [('internal_reference', 'Internal Reference', 'text'), ('product_name', 'Product Name', 'text'), ('brand', 'Brand', 'text'), ('uom', 'UOM', 'text'), ('current_qty', 'Total Closing Qty', 'number'), ('current_value', 'Total Closing Value', 'amount'), ('closing_avg_cost', 'Closing Avg. Cost', 'amount'), ('qty_0_30', labels[0] + ' Qty', 'number'), ('value_0_30', labels[0] + ' Value', 'amount'), ('qty_31_60', labels[1] + ' Qty', 'number'), ('value_31_60', labels[1] + ' Value', 'amount'), ('qty_61_90', labels[2] + ' Qty', 'number'), ('value_61_90', labels[2] + ' Value', 'amount'), ('qty_91_180', labels[3] + ' Qty', 'number'), ('value_91_180', labels[3] + ' Value', 'amount'), ('qty_181_365', labels[4] + ' Qty', 'number'), ('value_181_365', labels[4] + ' Value', 'amount'), ('qty_over_365', labels[5] + ' Qty', 'number'), ('value_over_365', labels[5] + ' Value', 'amount'), ('oldest_stock_date', 'Oldest Stock Date', 'text'), ('weighted_avg_age', 'Weighted Avg. Age (Days)', 'number'), ('aged_qty_180', 'Aged Qty >%s' % aged, 'number'), ('aged_value_180', 'Aged Value >%s' % aged, 'amount'), ('aged_percent_qty', 'Aged % Qty', 'percent'), ('aged_percent_value', 'Aged % Value', 'percent'), ('warehouse_qty_check', 'Warehouse Qty Check', 'number'), ('warehouse_value_check', 'Warehouse Value Check', 'amount'), ('no_movement_365', 'No Movement >%s' % last, 'text'), ('aging_risk_level', 'Risk Level', 'text'), ('opening_inventory_value', 'Opening Inventory Value', 'amount'), ('cogs_selected_period', 'COGS - Selected Period', 'amount'), ('average_inventory_value', 'Average Inventory Value', 'amount'), ('inventory_turnover_ratio', 'Inventory Turnover Ratio', 'number'), ('dio_days', 'DIO (Days)', 'number')]

    @api.model
    def export_excel(self, filters=None):
        filters = filters or {}
        report = self._get_report_data(filters)
        rows = report['rows']
        days = report['aging_period_days']
        view_mode = report['view_mode']
        columns = self._summary_excel_columns(days) if view_mode == 'summary' else self._detailed_excel_columns(days)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Product Aging Summary' if view_mode == 'summary' else 'Inventory Aging Detail')
        navy, navy_light, gold, gold_light, white, border = '#243746', '#36556C', '#D8A928', '#F8EDCC', '#FFFFFF', '#D9E0E4'
        title_fmt = workbook.add_format({'bold': True, 'font_size': 18, 'font_color': white, 'bg_color': navy, 'align': 'left', 'valign': 'vcenter'})
        header_fmt = workbook.add_format({'bold': True, 'font_color': white, 'bg_color': navy_light, 'border': 1, 'border_color': gold, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        text_fmt = workbook.add_format({'border': 1, 'border_color': border, 'align': 'center', 'valign': 'vcenter'})
        product_fmt = workbook.add_format({'border': 1, 'border_color': border, 'align': 'left', 'valign': 'vcenter'})
        num_fmt = workbook.add_format({'border': 1, 'border_color': border, 'num_format': '#,##0.00', 'align': 'center'})
        pct_fmt = workbook.add_format({'border': 1, 'border_color': border, 'num_format': '0.00%', 'align': 'center'})
        total_label = workbook.add_format({'bold': True, 'font_color': white, 'bg_color': navy, 'border': 1, 'border_color': gold, 'align': 'center'})
        total_num = workbook.add_format({'bold': True, 'font_color': navy, 'bg_color': gold_light, 'border': 1, 'border_color': gold, 'num_format': '#,##0.00', 'align': 'center'})
        total_empty = workbook.add_format({'bg_color': gold_light, 'border': 1, 'border_color': gold})
        risk = {
            'LOW': workbook.add_format({'border': 1, 'align': 'center', 'bold': True, 'font_color': '#2E7D32', 'bg_color': '#E8F5E9'}),
            'MEDIUM': workbook.add_format({'border': 1, 'align': 'center', 'bold': True, 'font_color': '#8B6900', 'bg_color': '#FFF4D7'}),
            'HIGH': workbook.add_format({'border': 1, 'align': 'center', 'bold': True, 'font_color': '#B25700', 'bg_color': '#FFF0E4'}),
            'CRITICAL': workbook.add_format({'border': 1, 'align': 'center', 'bold': True, 'font_color': '#B3261E', 'bg_color': '#FDE8E8'}),
        }
        title = 'Odoo 18 | Product Inventory Aging Summary + Turnover KPIs' if view_mode == 'summary' else 'Internal Inventory Aging Detail'
        sheet.merge_range(0, 0, 0, len(columns) - 1, title, title_fmt)
        sheet.set_row(0, 30)
        sheet.write(1, 0, 'Aging Date', header_fmt)
        sheet.write(1, 1, report['aging_date'].isoformat(), text_fmt)
        sheet.write(1, 2, 'Scope', header_fmt)
        sheet.write(1, 3, 'Internal Locations Only', text_fmt)
        sheet.write(2, 0, 'View', header_fmt)
        sheet.write(2, 1, view_mode.title(), text_fmt)
        sheet.write(2, 2, 'Aging Period Days', header_fmt)
        sheet.write(2, 3, days, text_fmt)
        header_row = 4
        for col, (_key, label, _type) in enumerate(columns):
            sheet.write(header_row, col, label, header_fmt)
        sheet.set_row(header_row, 38)
        row_no = header_row + 1
        for row in rows:
            for col, (key, _label, value_type) in enumerate(columns):
                value = row.get(key)
                if value is False or value is None:
                    value = ''
                fmt = risk.get(value, text_fmt) if key == 'aging_risk_level' else product_fmt if key == 'product_name' else pct_fmt if value_type == 'percent' else num_fmt if value_type in ('number', 'amount') else text_fmt
                sheet.write(row_no, col, value, fmt)
            row_no += 1
        totals = self._column_totals(rows)
        for col, (key, _label, _type) in enumerate(columns):
            if col == 0:
                sheet.write(row_no, col, 'TOTAL', total_label)
            elif key in totals:
                sheet.write(row_no, col, totals[key], total_num)
            else:
                sheet.write(row_no, col, '', total_empty)
        sheet.freeze_panes(header_row + 1, 2)
        if rows:
            sheet.autofilter(header_row, 0, row_no - 1, len(columns) - 1)
        sheet.set_column(0, 0, 18)
        sheet.set_column(1, 1, 42)
        sheet.set_column(2, len(columns) - 1, 17)
        workbook.close()
        output.seek(0)
        attachment = self.env['ir.attachment'].create({'name': 'Inventory_Aging_%s_%s.xlsx' % (view_mode.title(), report['aging_date'].isoformat()), 'type': 'binary', 'datas': base64.b64encode(output.read()), 'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'})
        return {'type': 'ir.actions.act_url', 'url': '/web/content/%s?download=true' % attachment.id, 'target': 'self'}