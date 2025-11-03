# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api,_
from num2words import num2words


class ExteriorPurchaseOrderView(models.AbstractModel):
    _name = "report.gs_purchase_tracking_v15.exterior_purchase_order_report"
    _description = "Exterior Purchase Order Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = []
        docs2 = []
        exterior_purchase = self.env['gs.purchase.tracking'].search([('id', '=', docids)])

        for child_ids in exterior_purchase.partner_id.child_ids:
            docs2.append({
                'child_name': child_ids.name,
                'child_phone': child_ids.phone,
                'child_email': child_ids.email,

            })

        for exterior in exterior_purchase.order_line_tracking:
            docs.append({
                'product_id': exterior.product_id.name,
                'name': exterior.product_id.description_purchase,
                'barcode': exterior.product_id.barcode,
                'date_planned': exterior.date_planned,
                'product_qty': exterior.product_qty,
                'shipment': exterior.shipment,
                'under_shipment': exterior.under_shipment,
                'sh_sec_qty': exterior.sh_sec_qty,
                'sh_sec_uom': exterior.sh_sec_uom.name,
                'product_uom': exterior.product_uom.name,
                'price_unit': exterior.price_unit,
                'taxes_id': exterior.taxes_id.name,
                'price_subtotal': exterior.price_subtotal,

            })
        address = " "
        if exterior_purchase.partner_id.street:
            address += exterior_purchase.partner_id.street + " / "
        if exterior_purchase.partner_id.street2:
            address += exterior_purchase.partner_id.street2 + " / "
        if exterior_purchase.partner_id.city:
            address += exterior_purchase.partner_id.city + " / "
        if exterior_purchase.partner_id.state_id:
            address += exterior_purchase.partner_id.state_id.name + " / "
        if exterior_purchase.partner_id.country_id:
            address += exterior_purchase.partner_id.country_id.name + " / "
        num_word = ''
        if self.env.lang == 'en_US':
            num_word = num2words(exterior_purchase.amount_total, lang='en_US') + _(" only")
        if self.env.lang == 'ar_001':
            num_word = num2words(exterior_purchase.amount_total, lang='ar_001') + _(" فقط ")

        return {
            'docs': docs,
            'docs2': docs2,
            'company_logo': exterior_purchase.company_id.logo,
            'company_registry': exterior_purchase.company_id.company_registry,
            'vat_no': exterior_purchase.company_id.vat,
            'branch_id': self.env.user.branch_id.id,
            'ref': exterior_purchase.partner_ref,
            'date': exterior_purchase.date_order,
            'city': exterior_purchase.city,
            'port': exterior_purchase.port,

            'partner_id': exterior_purchase.partner_id.name if exterior_purchase.partner_id.name else " ",
            'email': exterior_purchase.partner_id.email if exterior_purchase.partner_id.email else " ",
            'phone': exterior_purchase.partner_id.phone if exterior_purchase.partner_id.phone else " ",
            'address': address if address else " ",

            'name': exterior_purchase.name if exterior_purchase.name else " ",
            'partner_ref': exterior_purchase.partner_ref if exterior_purchase.partner_ref else " ",
            'currency_id': exterior_purchase.currency_id.name if exterior_purchase.currency_id.name else " ",
            'picking_type_id': exterior_purchase.picking_type_id.name if exterior_purchase.picking_type_id.name else " ",
            'date_order': exterior_purchase.date_order if exterior_purchase.date_order else " ",
            'date_planned': exterior_purchase.date_planned if exterior_purchase.date_planned else " ",
            'company_name': exterior_purchase.company_id.name if exterior_purchase.company_id.name else " ",
            'user_id': exterior_purchase.user_id.name if exterior_purchase.user_id.name else " ",
            'origin': exterior_purchase.origin if exterior_purchase.origin else " ",
            'payment_term_id': exterior_purchase.payment_term_id.name if exterior_purchase.payment_term_id.name else " ",
            'incoterm_id': exterior_purchase.incoterm_id.name if exterior_purchase.incoterm_id.name else " ",
            'amount_total': exterior_purchase.amount_total if exterior_purchase.amount_total else " ",
            'num_word': num_word,

        }
