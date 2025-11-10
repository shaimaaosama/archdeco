# -*- coding: utf-8 -*-
import json
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError


class GsPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    shipment_tracking_id = fields.Many2one('gs.shipment.tracking', string='Shipment')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    analytic_tag_id = fields.Many2one('account.analytic.tag', string='Analytic Tag')

    price_basis = fields.Char()
    offer_validity= fields.Char()
    work_period = fields.Char()
    project_location = fields.Char()
    project = fields.Char()
    matrial = fields.Char()
    install = fields.Char()
    payment_terms = fields.Text()
    bank_detials = fields.Text()
    special_conditions = fields.Text()
    client_order_ref = fields.Text()

class GsPurchaseLineOrder(models.Model):
    _inherit = 'purchase.order.line'

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        aml_currency = move and move.currency_id or self.currency_id
        date = move and move.date or fields.Date.today()
        if self.order_id.analytic_account_id and self.order_id.analytic_tag_id:
            res = {
                'display_type': self.display_type,
                'sequence': self.sequence,
                'name': '%s: %s' % (self.order_id.name, self.name),
                'product_id': self.product_id.id,
                'product_uom_id': self.product_uom.id,
                'quantity': self.qty_to_invoice,
                'price_unit': self.currency_id._convert(self.price_unit, aml_currency, self.company_id, date, round=False),
                'tax_ids': [(6, 0, self.taxes_id.ids)],
                'analytic_distribution': self.analytic_distribution,
                'purchase_line_id': self.id,
            }
        elif self.order_id.analytic_account_id and not self.order_id.analytic_tag_id:
            res = {
                'display_type': self.display_type,
                'sequence': self.sequence,
                'name': '%s: %s' % (self.order_id.name, self.name),
                'product_id': self.product_id.id,
                'product_uom_id': self.product_uom.id,
                'quantity': self.qty_to_invoice,
                'price_unit': self.currency_id._convert(self.price_unit, aml_currency, self.company_id, date, round=False),
                'tax_ids': [(6, 0, self.taxes_id.ids)],
                'analytic_distribution': self.analytic_distribution,
                'purchase_line_id': self.id,
            }
        elif not self.order_id.analytic_account_id and self.order_id.analytic_tag_id:
            res = {
                'display_type': self.display_type,
                'sequence': self.sequence,
                'name': '%s: %s' % (self.order_id.name, self.name),
                'product_id': self.product_id.id,
                'product_uom_id': self.product_uom.id,
                'quantity': self.qty_to_invoice,
                'price_unit': self.currency_id._convert(self.price_unit, aml_currency, self.company_id, date, round=False),
                'tax_ids': [(6, 0, self.taxes_id.ids)],
                'analytic_distribution': self.analytic_distribution,
                'purchase_line_id': self.id,
            }
        else:
            res = {
                'display_type': self.display_type,
                'sequence': self.sequence,
                'name': '%s: %s' % (self.order_id.name, self.name),
                'product_id': self.product_id.id,
                'product_uom_id': self.product_uom.id,
                'quantity': self.qty_to_invoice,
                'price_unit': self.currency_id._convert(self.price_unit, aml_currency, self.company_id, date, round=False),
                'tax_ids': [(6, 0, self.taxes_id.ids)],
                'analytic_distribution': self.analytic_distribution,
                'purchase_line_id': self.id,
            }
        if not move:
            return res

        if self.currency_id == move.company_id.currency_id:
            currency = False
        else:
            currency = move.currency_id

        res.update({
            'move_id': move.id,
            'currency_id': currency and currency.id or False,
            'date_maturity': move.invoice_date_due,
            'partner_id': move.partner_id.id,
        })
        return res


class GsShipmentTracking(models.Model):
    _name = 'gs.shipment.tracking'
    _description = 'Shipment Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

    def action_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})
        return True

    def action_submit(self):
        for rec in self:
            rec.write({'state': 'submit'})
        return True

    def action_confirmed(self):
        for rec in self:
            rec.write({'state': 'confirmed'})
        return True

    def action_booking(self):
        for rec in self:
            rec.write({'state': 'booking'})
        return True

    def action_booked(self):
        for rec in self:
            rec.write({'state': 'booked'})
        return True

    def action_loading(self):
        for rec in self:
            rec.write({'state': 'loading'})
        return True

    def action_loaded(self):
        for rec in self:
            rec.write({'state': 'loaded'})
        return True

    def action_on_board(self):
        for rec in self:
            rec.write({'state': 'on_board'})
        return True

    def action_departed(self):
        for rec in self:
            rec.write({'state': 'departed'})
        return True

    def action_doc_collect(self):
        for rec in self:
            rec.write({'state': 'doc_collect'})
        return True

    def action_issue_insurance(self):
        for rec in self:
            rec.write({'state': 'issue_insurance'})
        return True

    def action_arrived(self):
        for rec in self:
            rec.write({'state': 'arrived'})
        return True

    def action_under_clearance(self):
        for rec in self:
            rec.write({'state': 'under_clearance'})
        return True

    def action_cleared(self):
        for rec in self:
            rec.write({'state': 'cleared'})
        return True

    def action_paneling_delivery(self):
        for rec in self:
            rec.write({'state': 'paneling_delivery'})
        return True

    def action_received(self):
        for rec in self:
            rec.write({'state': 'received'})
        return True

    def action_view_purchase_order(self):
        return {
            'name': _('Purchase Order'),
            'domain': [('shipment_tracking_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'purchase.order',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }
    purchase_order_count = fields.Integer(compute='get_purchase_order_count')

    def get_purchase_order_count(self):
        count = self.env['purchase.order'].search_count([('shipment_tracking_id', '=', self.id)])
        self.purchase_order_count = count

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('gs.shipment.tracking.sequence') or _('New')
        result = super(GsShipmentTracking, self).create(vals)
        result.action_crate_shipment_clearance()
        return result

    picking_id = fields.Many2many('stock.picking', string='Receipt')
    partner_id = fields.Many2many('res.partner', string='Vendor')
    name = fields.Char('Reference', required=True, copy=False, readonly=True,
                       index=True, default=lambda self: _('New'))
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('submit', 'Submit'),
        ('confirmed', 'Confirmed'),
        ('booking', 'Booking'),
        ('booked', 'Booked'),
        ('loading', 'Loading'),
        ('loaded', 'Loaded'),
        ('on_board', 'On Board'),
        ('departed', 'Departed'),
        ('doc_collect', 'Doc Collect'),
        ('issue_insurance', 'Issue Insurance'),
        ('arrived', 'Arrived'),
        ('under_clearance', 'Under Clearance'),
        ('cleared', 'Cleared'),
        ('paneling_delivery', 'Pending Delivery'),
        ('received', 'Received'),
        ('cancel', 'Cancelled'),
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company.id)
    shipment_line_tracking = fields.One2many('gs.shipment.line.tracking', 'shipment_id', store=True)
    user_id = fields.Many2one(
        'res.users', string='Purchase Representative', index=True, tracking=True,
        default=lambda self: self.env.user, check_company=True)
    origin = fields.Char('Source Document', copy=False,
                         help="Reference of the document that generated this purchase order "
                              "request (e.g. a sales order)")
    incoterm_id = fields.Many2one('account.incoterms', 'Incoterm',
                                  help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Terms',
                                      domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    tax_country_id = fields.Many2one(
        comodel_name='res.country',
        compute='_compute_tax_country_id',
        compute_sudo=True,
        help="Technical field to filter the available taxes depending on the fiscal country and fiscal position.")
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position',
                                         domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    date_order = fields.Datetime('Order Deadline', default=fields.Datetime.now)
    date_planned = fields.Datetime(string='Receipt Date', )
    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', required=True,
                                      domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
                                      help="This will determine operation type of incoming shipment")
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',
                                     tracking=True)
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')
    tax_totals_json = fields.Char()  # compute='_compute_tax_totals_json'
    shipment_documents_ids = fields.One2many('gs.shipment.documents.lines', 'link_id', string='Shipment Documents')
    clearance_documents_ids = fields.One2many('gs.clearance.documents.lines', 'link_id', string='Clearance Documents')
    comparison_sheet_ids = fields.One2many('gs.comparison.sheet.lines', 'link_id', string='Comparison Sheet')
    partner_ref = fields.Char('Vendor Reference',)
    is_approved_line = fields.Boolean()

    booking_reference = fields.Char('Booking Reference',)
    shipping_line = fields.Char('Shipping Line',)
    pl_reference = fields.Char('BL Reference',)
    forwarder_name = fields.Char('Forwarder Name',)
    customs_statement = fields.Char('Customs Statement',)

    etd = fields.Date(string='ETD', )
    eta = fields.Date(string='ETA', )
    e_trans_time = fields.Integer(string='Trans Time',)

    @api.onchange('etd', 'eta')
    def _get_available_days_etd_eta(self):
        if self.etd and self.eta:
            wd_diff = fields.Datetime.from_string(self.eta) - fields.Datetime.from_string(self.etd)
            self.e_trans_time = wd_diff.days

    atd = fields.Date(string='ATD', )
    ata = fields.Date(string='ATA', )
    a_trans_time = fields.Integer(string='Trans Time',)

    @api.onchange('atd', 'ata')
    def _get_available_days_atd_ata(self):
        if self.atd and self.ata:
            wd_diff = fields.Datetime.from_string(self.ata) - fields.Datetime.from_string(self.atd)
            self.a_trans_time = wd_diff.days

    atr = fields.Date(string='ATR', )
    roll_over = fields.Integer(string='Roll Over', )
    r_trans_time = fields.Integer(string='Trans Time',)

    @api.onchange('atr', 'roll_over')
    def _get_available_days_atr_roll_over(self):
        if self.atr and self.atd and self.e_trans_time:
            wd_diff = fields.Datetime.from_string(self.atr) - fields.Datetime.from_string(self.atd)
            if self.e_trans_time:
                days = wd_diff.days
                self.roll_over = days - self.e_trans_time

    is_cancel = fields.Boolean(compute="_get_default_cancel")
    is_draft = fields.Boolean(compute="_get_default_draft")
    is_submit = fields.Boolean(compute="_get_default_submit")
    is_confirmed = fields.Boolean(compute="_get_default_confirmed")
    is_booking = fields.Boolean(compute="_get_default_booking")
    is_booked = fields.Boolean(compute="_get_default_booked")
    is_loading = fields.Boolean(compute="_get_default_loading")
    is_loaded = fields.Boolean(compute="_get_default_loaded")
    is_on_board = fields.Boolean(compute="_get_default_on_board")
    is_departed = fields.Boolean(compute="_get_default_departed")
    is_doc_collect = fields.Boolean(compute="_get_default_doc_collect")
    is_issue_insurance = fields.Boolean(compute="_get_default_issue_insurance")
    is_arrived = fields.Boolean(compute="_get_default_arrived")
    is_under_clearance = fields.Boolean(compute="_get_default_under_clearance")
    is_cleared = fields.Boolean(compute="_get_default_cleared")
    is_paneling_delivery = fields.Boolean(compute="_get_default_paneling_delivery")
    is_received = fields.Boolean(compute="_get_default_received")
    is_finish = fields.Boolean()

    is_bol_cleared = fields.Boolean(compute="_get_default_receipt")

    def _get_default_receipt(self):
        for rec in self:
            rec.is_bol_cleared = False
            if rec.state == 'cleared':
                for line in rec.picking_id:
                    line.state = 'assigned'
                rec.is_bol_cleared = True

    @api.depends('shipment_line_tracking.taxes_id', 'shipment_line_tracking.price_subtotal', 'amount_total',
                 'amount_untaxed')
    def _compute_tax_totals_json(self):
        def compute_taxes(shipment_line_tracking):
            return shipment_line_tracking.taxes_id._origin.compute_all(
                **shipment_line_tracking._prepare_compute_all_values())

        account_move = self.env['account.move']
        for order in self:
            for partner in order.partner_id:
                tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(
                    order.shipment_line_tracking, compute_taxes)
                tax_totals = account_move._get_tax_totals(partner, tax_lines_data, order.amount_total,
                                                          order.amount_untaxed, order.currency_id)
                order.tax_totals_json = json.dumps(tax_totals)

    @api.depends('shipment_line_tracking.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.shipment_line_tracking:
                line._compute_amount()
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            currency = order.currency_id or order.partner_id.property_purchase_currency_id or self.env.company.currency_id
            order.update({
                'amount_untaxed': currency.round(amount_untaxed),
                'amount_tax': currency.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    def action_readonly_approved(self):
        for rec in self.comparison_sheet_ids:
            rec.readonly_approved = False

    @api.depends('company_id.account_fiscal_country_id', 'fiscal_position_id.country_id',
                 'fiscal_position_id.foreign_vat')
    def _compute_tax_country_id(self):
        for record in self:
            if record.fiscal_position_id.foreign_vat:
                record.tax_country_id = record.fiscal_position_id.country_id
            else:
                record.tax_country_id = record.company_id.account_fiscal_country_id

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        for rec in self:
            rec.is_finish = False
            if rec.picking_id:
                rec.partner_id += rec.picking_id.partner_id
                rec.shipment_line_tracking = [(5, 0, 0)]

    def action_crate_shipment_clearance(self):
        for rec in self:
            shipment_documents = self.env['gs.shipment.documents'].search([])
            clearance_documents = self.env['gs.clearance.documents'].search([])
            lines = [(5, 0, 0)]
            for line in shipment_documents:
                val = {
                    'name': line.name,
                    'is_required': line.is_required,
                    'product_id': line.product_id.id,
                }
                lines.append((0, 0, val))
                rec.shipment_documents_ids = lines

            lines = [(5, 0, 0)]
            for line in clearance_documents:
                val = {
                    'name': line.name,
                    'is_required': line.is_required,
                    'product_id': line.product_id.id,
                }
                lines.append((0, 0, val))
                rec.clearance_documents_ids = lines

    def action_crate_one2many(self):
        for rec in self:
            rec.is_finish = True
            lines = []
            for picking in rec.picking_id:
                for pro in picking.move_ids_without_package:
                    if pro.product_uom_qty == 0:
                        pass
                    else:
                        val = {
                            'id_field': pro.id if pro.id else False,
                            'product_id': pro.product_id.id if pro.product_id.id else False,
                            'name': pro.description_picking if pro.description_picking else False,
                            'company_id': pro.company_id.id if pro.company_id.id else False,
                            'product_type': pro.product_type if pro.product_type else False,
                            'date_planned': pro.date if pro.date else False,
                            'product_qty': pro.product_uom_qty if pro.product_uom_qty else False,
                            'product_uom': pro.product_uom.id if pro.product_uom.id else False,
                            'sh_is_secondary_unit': pro.sh_is_secondary_unit if pro.sh_is_secondary_unit else False,
                            'sh_sec_qty': pro.sh_sec_qty if pro.sh_sec_qty else False,
                            'sh_sec_uom': pro.sh_sec_uom.id if pro.sh_sec_uom.id else False,
                            'location_id': pro.location_id.id if pro.location_id.id else False,
                            'location_dest_id': pro.location_dest_id.id if pro.location_dest_id.id else False,
                            'price_unit': 0,
                        }
                        lines.append((0, 0, val))
            print("lines", lines)
            rec.shipment_line_tracking = lines

    # def action_crate_one2many(self):
    #     for rec in self:
    #         rec.is_finish = True
    #         line_ids = []
    #         for shipment in rec.shipment_line_tracking:
    #             val = {
    #                 'id': shipment.id_field if shipment.id_field else False,
    #             }
    #             line_ids.append(val)
    #         picking_ids = []
    #         for picking in rec.picking_id:
    #             for pro in picking.move_ids_without_package:
    #                 val = {
    #                     'id': pro.id if pro.id else False,
    #                 }
    #                 picking_ids.append(val)
    #
    #         if line_ids:
    #             for lin in line_ids:
    #                 lines = []
    #                 for picking in rec.picking_id:
    #                     for pro in picking.move_ids_without_package:
    #                         if int(pro.id) == int(lin['id']):
    #                             pass
    #                         else:
    #                             val = {
    #                                 'id_field': pro.id if pro.id else False,
    #                                 'product_id': pro.product_id.id if pro.product_id.id else False,
    #                                 'name': pro.description_picking if pro.description_picking else False,
    #                                 'company_id': pro.company_id.id if pro.company_id.id else False,
    #                                 'product_type': pro.product_type if pro.product_type else False,
    #                                 'date_planned': pro.date if pro.date else False,
    #                                 'product_qty': pro.product_uom_qty if pro.product_uom_qty else False,
    #                                 'product_uom': pro.product_uom.id if pro.product_uom.id else False,
    #                                 'sh_is_secondary_unit': pro.sh_is_secondary_unit if pro.sh_is_secondary_unit else False,
    #                                 'sh_sec_qty': pro.sh_sec_qty if pro.sh_sec_qty else False,
    #                                 'sh_sec_uom': pro.sh_sec_uom.id if pro.sh_sec_uom.id else False,
    #                                 'location_id': pro.location_id.id if pro.location_id.id else False,
    #                                 'location_dest_id': pro.location_dest_id.id if pro.location_dest_id.id else False,
    #                                 'price_unit': 0,
    #                             }
    #                             lines.append((0, 0, val))
    #         else:
    #             lines = []
    #             for picking in rec.picking_id:
    #                 for pro in picking.move_ids_without_package:
    #                     val = {
    #                         'id_field': pro.id if pro.id else False,
    #                         'product_id': pro.product_id.id if pro.product_id.id else False,
    #                         'name': pro.description_picking if pro.description_picking else False,
    #                         'company_id': pro.company_id.id if pro.company_id.id else False,
    #                         'product_type': pro.product_type if pro.product_type else False,
    #                         'date_planned': pro.date if pro.date else False,
    #                         'product_qty': pro.product_uom_qty if pro.product_uom_qty else False,
    #                         'product_uom': pro.product_uom.id if pro.product_uom.id else False,
    #                         'sh_is_secondary_unit': pro.sh_is_secondary_unit if pro.sh_is_secondary_unit else False,
    #                         'sh_sec_qty': pro.sh_sec_qty if pro.sh_sec_qty else False,
    #                         'sh_sec_uom': pro.sh_sec_uom.id if pro.sh_sec_uom.id else False,
    #                         'location_id': pro.location_id.id if pro.location_id.id else False,
    #                         'location_dest_id': pro.location_dest_id.id if pro.location_dest_id.id else False,
    #                         'price_unit': 0,
    #                     }
    #                     lines.append((0, 0, val))
    #             print("lines", lines)
    #             rec.shipment_line_tracking = lines

    def _get_default_submit(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_submit = False
            if permission:
                if user in permission.submit_st_id.ids:
                    rec.is_submit = True

    def _get_default_cancel(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_cancel = False
            if permission:
                if user in permission.cancel_st_id.ids:
                    rec.is_cancel = True

    def _get_default_draft(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_draft = False
            if permission:
                if user in permission.draft_st_id.ids:
                    rec.is_draft = True

    def _get_default_confirmed(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_confirmed = False
            if permission:
                if user in permission.confirmed_st_id.ids:
                    rec.is_confirmed = True

    def _get_default_booking(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_booking = False
            if permission:
                if user in permission.booking_st_id.ids:
                    rec.is_booking = True

    def _get_default_booked(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_booked = False
            if permission:
                if user in permission.booked_st_id.ids:
                    rec.is_booked = True

    def _get_default_loading(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_loading = False
            if permission:
                if user in permission.loading_st_id.ids:
                    rec.is_loading = True

    def _get_default_loaded(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_loaded = False
            if permission:
                if user in permission.loaded_st_id.ids:
                    rec.is_loaded = True

    def _get_default_on_board(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_on_board = False
            if permission:
                if user in permission.on_board_st_id.ids:
                    rec.is_on_board = True

    def _get_default_departed(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_departed = False
            if permission:
                if user in permission.departed_st_id.ids:
                    rec.is_departed = True

    def _get_default_doc_collect(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_doc_collect = False
            if permission:
                if user in permission.doc_collect_st_id.ids:
                    rec.is_doc_collect = True

    def _get_default_issue_insurance(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_issue_insurance = False
            if permission:
                if user in permission.issue_insurance_st_id.ids:
                    rec.is_issue_insurance = True

    def _get_default_arrived(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_arrived = False
            if permission:
                if user in permission.arrived_st_id.ids:
                    rec.is_arrived = True

    def _get_default_under_clearance(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_under_clearance = False
            if permission:
                if user in permission.under_clearance_st_id.ids:
                    rec.is_under_clearance = True

    def _get_default_cleared(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_cleared = False
            if permission:
                if user in permission.cleared_st_id.ids:
                    rec.is_cleared = True

    def _get_default_paneling_delivery(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_paneling_delivery = False
            if permission:
                if user in permission.paneling_delivery_st_id.ids:
                    rec.is_paneling_delivery = True

    def _get_default_received(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_shipment_tracking')], limit=1)
            rec.is_received = False
            if permission:
                if user in permission.received_st_id.ids:
                    rec.is_received = True


class ShipmentLineTracking(models.Model):
    _name = 'gs.shipment.line.tracking'

    shipment_id = fields.Many2one('gs.shipment.tracking', string='Tracking Reference', index=True, required=True,
                                  ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)],
                                 change_default=True)
    product_type = fields.Selection(related='product_id.type', readonly=True)
    name = fields.Text(string='Description', related='product_id.description_purchase')
    date_planned = fields.Datetime(string='Delivery Date', index=True, default=fields.Datetime.now,
                                   help="Delivery date expected from vendor. This date respectively defaults to vendor pricelist lead time then today's date.")
    sequence = fields.Integer(string='Sequence', default=10)
    id_field = fields.Char()
    product_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True)
    sh_sec_qty = fields.Float("Secondary Qty", digits='Product Unit of Measure')
    sh_sec_uom = fields.Many2one("uom.uom", 'Secondary UOM')
    sh_is_secondary_unit = fields.Boolean("Related Sec Unit", related="product_id.sh_is_secondary_unit")
    category_id = fields.Many2one("uom.category", "Purchase UOM Category", related="product_uom.category_id")
    taxes_id = fields.Many2many('account.tax', string='Taxes',
                                domain=['|', ('active', '=', False), ('active', '=', True)])
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]", related='product_id.uom_po_id')
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    price_unit = fields.Float(string='Unit Price', required=True, digits='Product Price')

    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=True)
    company_id = fields.Many2one('res.company', related='shipment_id.company_id', string='Company', store=True,
                                 readonly=True)
    currency_id = fields.Many2one(related='shipment_id.currency_id', store=True, string='Currency', readonly=True)
    location_id = fields.Many2one('stock.location', 'Source Location', )
    location_dest_id = fields.Many2one('stock.location', 'Destination Location', )
    shipment = fields.Float(string='Shipment')
    under_shipment = fields.Float(string='Under Shipment')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

    @api.onchange('shipment')
    def onchange_shipment(self):
        if self.shipment and self.product_qty:
            if self.shipment > self.product_qty:
                raise ValidationError(_("Quantity Less Than Shipment"))

    @api.onchange('product_qty', 'product_uom')
    def onchange_product_uom_qty_sh(self):
        if self and self.sh_is_secondary_unit and self.sh_sec_uom:
            self.sh_sec_qty = self.product_uom._compute_quantity(
                self.product_qty, self.sh_sec_uom
            )
        float_num = self.sh_sec_qty - int(self.sh_sec_qty)
        int_num = int(self.sh_sec_qty)
        if float_num > 0.25:
            int_num += 1
            self.sh_sec_qty = int_num
        else:
            self.sh_sec_qty = int(self.sh_sec_qty)

    @api.onchange('sh_sec_qty', 'sh_sec_uom')
    def onchange_sh_sec_qty_sh(self):
        if self and self.sh_is_secondary_unit and self.product_uom:
            self.product_qty = self.sh_sec_uom._compute_quantity(
                self.sh_sec_qty, self.product_uom
            )

    @api.onchange('product_id')
    def onchange_secondary_uom(self):
        if self:
            for rec in self:
                if rec.product_id and rec.product_id.sh_is_secondary_unit and rec.product_id.uom_id:
                    rec.sh_sec_uom = rec.product_id.sh_secondary_uom.id
                elif not rec.product_id.sh_is_secondary_unit:
                    rec.sh_sec_uom = False
                    rec.sh_sec_qty = 0.0

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            taxes = line.taxes_id.compute_all(**line._prepare_compute_all_values())
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    def _prepare_compute_all_values(self):
        self.ensure_one()
        return {
            'price_unit': self.price_unit,
            'currency': self.shipment_id.currency_id,
            'quantity': self.product_qty,
            'product': self.product_id,
            'partner': self.shipment_id.partner_id,
        }


class GsShipmentDocumentsLines(models.Model):
    _name = 'gs.shipment.documents.lines'
    _description = 'Shipment Documents Lines'

    link_id = fields.Many2one('gs.shipment.tracking')
    name = fields.Char()
    link = fields.Char()
    partner_id = fields.Many2one('res.partner',)
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.company.currency_id.id)
    amount = fields.Float(string='Amount',)
    date = fields.Date(string='Date',)
    is_required = fields.Boolean(string='Is Required?',)
    hide = fields.Boolean()
    product_id = fields.Many2one('product.product', string="Product",)

    def create_purchase_order(self):
        for rec in self:
            rec.hide = True
            name = ''
            if rec.product_id.default_code:
                name += '[' + rec.product_id.default_code + ']' + rec.product_id.name
            else:
                name += rec.product_id.name
            vals = {
                'shipment_tracking_id': rec.link_id.id,
                'origin': rec.link_id.name,
                'partner_id': rec.partner_id.id,
                'currency_id': rec.currency_id.id,
                'partner_ref': rec.name,
                'date_order': fields.Datetime.now(),
                'picking_type_id': rec.link_id.picking_type_id.id,
                'order_line': [
                    (0, 0, {
                        'name': name,
                        'product_id': rec.product_id.id,
                        'product_qty': 1,
                        'price_unit': rec.amount,
                        'date_planned': fields.Datetime.now(),
                    })]
            }
            purchase = self.env['purchase.order'].create(vals)
            action = {
                'name': _('Purchase Order'),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'res_id': purchase.id,
                'context': {'create': False},
            }
            return action


class GsClearanceDocumentsLines(models.Model):
    _name = 'gs.clearance.documents.lines'
    _description = 'Clearance Documents Lines'

    link_id = fields.Many2one('gs.shipment.tracking')
    name = fields.Char()
    link = fields.Char()
    partner_id = fields.Many2one('res.partner',)
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.company.currency_id.id)
    amount = fields.Float(string='Amount',)
    date = fields.Date(string='Date',)
    is_required = fields.Boolean(string='Is Required?',)
    hide = fields.Boolean()
    product_id = fields.Many2one('product.product', string="Product", )

    def create_purchase_order(self):
        for rec in self:
            rec.hide = True
            name = ''
            if rec.product_id.default_code:
                name += '[' + rec.product_id.default_code + ']' + rec.product_id.name
            else:
                name += rec.product_id.name
            vals = {
                'shipment_tracking_id': rec.link_id.id,
                'partner_id': rec.partner_id.id,
                'origin': rec.link_id.name,
                'currency_id': rec.currency_id.id,
                'partner_ref': rec.name,
                'date_order': fields.Datetime.now(),
                'picking_type_id': rec.link_id.picking_type_id.id,
                'order_line': [
                    (0, 0, {
                        'name': name,
                        'product_id': rec.product_id.id,
                        'product_qty': 1,
                        'price_unit': rec.amount,
                        'date_planned': fields.Datetime.now(),
                    })]
            }
            purchase = self.env['purchase.order'].create(vals)
            action = {
                'name': _('Purchase Order'),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'res_id': purchase.id,
                'context': {'create': False},
            }
            return action


class GsComparisonSheetLines(models.Model):
    _name = 'gs.comparison.sheet.lines'
    _description = 'Comparison Sheet Lines'

    link_id = fields.Many2one('gs.shipment.tracking')
    name = fields.Char()
    amount = fields.Float(string='Amount',)
    date = fields.Char(string='Transit Time',)
    pol = fields.Char(string="POL")
    port = fields.Char(string="POD")
    free_time = fields.Char(string="Free Time")
    etd = fields.Date(string="ETD")
    shipping_line = fields.Char(string="Shipping Line")
    is_approved = fields.Boolean(string='approved?',)
    readonly_approved = fields.Boolean(default=True)

    def action_approved(self):
        self.link_id.action_readonly_approved()
        self.link_id.is_approved_line = True
        self.is_approved = True
