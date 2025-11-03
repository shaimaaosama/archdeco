# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ShipmentTrackingReportView(models.AbstractModel):
    _name = "report.gs_purchase_tracking_v15.shipment_tracking_report"
    _description = "Shipment Tracking Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = []
        docs2 = []
        docs3 = []
        docs4 = []
        shipment_tracking = self.env['gs.shipment.tracking'].search([('id', '=', docids)])

        for shipment in shipment_tracking.shipment_line_tracking:
            docs.append({
                'product_id': shipment.product_id.name,
                'name': shipment.name,
                'date_planned': shipment.date_planned,
                'product_qty': shipment.product_qty,
                'sh_sec_qty': shipment.sh_sec_qty,
                'sh_sec_uom': shipment.sh_sec_uom.name,
                'product_uom': shipment.product_uom.name,
                'price_unit': shipment.price_unit,
                'taxes_id': shipment.taxes_id.name,
                'price_subtotal': shipment.price_subtotal,

            })

        for shipment_do in shipment_tracking.shipment_documents_ids:
            docs2.append({
                'name': shipment_do.name,
                'link': shipment_do.link,
                'currency_id': shipment_do.currency_id.name,
                'amount': shipment_do.amount,
                'date': shipment_do.date,
                'is_required': shipment_do.is_required,
            })

        for clearance in shipment_tracking.clearance_documents_ids:
            docs3.append({
                'name': clearance.name,
                'link': clearance.link,
                'currency_id': clearance.currency_id.name,
                'amount': clearance.amount,
                'date': clearance.date,
                'is_required': clearance.is_required,
            })
        picking_text = ''
        for picking in shipment_tracking.picking_id:
            picking_text += '( ' + picking.name + ' )'

        partner_text = ''
        for partner in shipment_tracking.partner_id:
            partner_text += '( ' + partner.name + ' )'

        for comparison in shipment_tracking.comparison_sheet_ids:
            if comparison.is_approved:
                docs4.append({
                    'name': comparison.name,
                    'amount': comparison.amount,
                    'pol': comparison.pol,
                    'port': comparison.port,
                    'free_time': comparison.free_time,
                    'etd': comparison.etd,
                    'shipping_line': comparison.shipping_line,
                    'date': comparison.date,
                    'is_approved': "True",

                })
            else:
                docs4.append({
                    'name': comparison.name,
                    'amount': comparison.amount,
                    'pol': comparison.pol,
                    'port': comparison.port,
                    'free_time': comparison.free_time,
                    'etd': comparison.etd,
                    'shipping_line': comparison.shipping_line,
                    'date': comparison.date,
                    'is_approved': "False",
                })
        return {
            'docs': docs,
            'docs2': docs2,
            'docs3': docs3,
            'docs4': docs4,

            'picking_id': picking_text if picking_text else " ",
            'partner_id': partner_text if partner_text else " ",
            'name': shipment_tracking.name if shipment_tracking.name else " ",
            'partner_ref': shipment_tracking.partner_ref if shipment_tracking.partner_ref else " ",
            'currency_id': shipment_tracking.currency_id.name if shipment_tracking.currency_id.name else " ",
            'picking_type_id': shipment_tracking.picking_type_id.name if shipment_tracking.picking_type_id.name else " ",
            'date_order': shipment_tracking.date_order if shipment_tracking.date_order else " ",
            'date_planned': shipment_tracking.date_planned if shipment_tracking.date_planned else " ",
            'company_name': shipment_tracking.company_id.name if shipment_tracking.company_id.name else " ",
            'user_id': shipment_tracking.user_id.name if shipment_tracking.user_id.name else " ",
            'origin': shipment_tracking.origin if shipment_tracking.origin else " ",
            'payment_term_id': shipment_tracking.payment_term_id.name if shipment_tracking.payment_term_id.name else " ",
            'incoterm_id': shipment_tracking.incoterm_id.name if shipment_tracking.incoterm_id.name else " ",
            'tax_totals_json': shipment_tracking.tax_totals_json if shipment_tracking.tax_totals_json else " ",

            'etd': shipment_tracking.etd if shipment_tracking.etd else " ",
            'eta': shipment_tracking.eta if shipment_tracking.eta else " ",
            'e_trans_time': shipment_tracking.e_trans_time if shipment_tracking.e_trans_time else " ",

            'atd': shipment_tracking.atd if shipment_tracking.atd else " ",
            'ata': shipment_tracking.ata if shipment_tracking.ata else " ",
            'a_trans_time': shipment_tracking.a_trans_time if shipment_tracking.a_trans_time else " ",

            'atr': shipment_tracking.atr if shipment_tracking.atr else " ",
            'roll_over': shipment_tracking.roll_over if shipment_tracking.roll_over else " ",

            'booking_reference': shipment_tracking.booking_reference if shipment_tracking.booking_reference else " ",
            'shipping_line': shipment_tracking.shipping_line if shipment_tracking.shipping_line else " ",
            'pl_reference': shipment_tracking.pl_reference if shipment_tracking.pl_reference else " ",
            'forwarder_name': shipment_tracking.forwarder_name if shipment_tracking.forwarder_name else " ",

        }
