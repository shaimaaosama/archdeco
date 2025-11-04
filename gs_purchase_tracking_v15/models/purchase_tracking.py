# -*- coding: utf-8 -*-
import json
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError


class GsStockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    tracking_id = fields.Many2one('gs.purchase.tracking', string="Purchase External")


class GsPurchaseTracking(models.Model):
    _name = 'gs.purchase.tracking'
    _description = 'Purchase Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

    def action_draft(self):
        self.is_finish = False
        self.write({'state': 'draft'})
        return True

    def action_submit(self):
        for rec in self:
            users = self.env['gs.purchase.tracking.permission'].search([('permission_type', '=', 'p_purchase_tracking')])
            for user in users.approve_t_id:
                rec.make_activity_user(user)
            rec.write({'state': 'submit'})
        return True

    def make_activity_user(self, user):
        date_deadline = fields.Date.today()
        note = _("Please Review This Purchase Tracking")
        summary = _("Purchase Tracking")

        self.sudo().activity_schedule(
            'mail.mail_activity_data_todo', date_deadline,
            note=note,
            user_id=user.id,
            res_id=self.id,
            summary=summary
        )

    def make_activity_receipt(self, user):
        date_deadline = fields.Date.today()
        note = _("You Have A New Receipt")
        summary = _("Purchase Tracking Receipt")

        self.sudo().activity_schedule(
            'mail.mail_activity_data_todo', date_deadline,
            note=note,
            user_id=user.id,
            res_id=self.id,
            summary=summary
        )

    def action_approved(self):
        for rec in self:
            rec.write({'state': 'approved'})
        return True

    def action_lock(self):
        for rec in self:
            rec.write({'state': 'locked'})
        return True

    def action_unlock(self):
        for rec in self:
            rec.write({'state': 'unlocked'})
        return True

    shipment_count = fields.Integer("Shipment count", compute='_compute_shipment_count')

    def action_view_shipment(self):
        pickings = self.env['stock.picking'].search([('tracking_id', '=', self.id)])
        shipments = self.env['gs.shipment.tracking'].search([])
        shipment_list = []
        for ship in shipments:
            picking_list = []
            for pic in pickings:
                for lin in ship.picking_id:
                    picking_list.append(lin.id)
                if pic.id in picking_list:
                    shipment_list.append(ship.id)

        return {
            'name': _('Shipment Tracking'),
            'domain': [('id', 'in', shipment_list)],
            'view_type': 'form',
            'res_model': 'gs.shipment.tracking',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def _compute_shipment_count(self):
        pickings = self.env['stock.picking'].search([('tracking_id', '=', self.id)])
        shipments = self.env['gs.shipment.tracking'].search([])
        shipment_list = []
        for ship in shipments:
            picking_list = []
            for pic in pickings:
                for lin in ship.picking_id:
                    picking_list.append(lin.id)
                if pic.id in picking_list:
                    shipment_list.append(ship.id)
        shipment_tracking = self.env['gs.shipment.tracking'].search_count([('id', 'in', shipment_list)])
        self.shipment_count = shipment_tracking

    def action_view_picking(self):
        pickings = self.env['stock.picking'].search([('tracking_id', '=', self.id)])
        return self._get_action_view_picking(pickings)

    def _get_action_view_picking(self, pickings):
        self.ensure_one()
        result = self.env["ir.actions.actions"]._for_xml_id('stock.action_picking_tree_all')
        # override the context to get rid of the default filtering on operation type
        result['context'] = {'default_tracking_id': self.id, 'default_origin': self.name, 'default_picking_type_id': self.picking_type_id.id}
        # choose the view_mode accordingly
        if not pickings or len(pickings) > 1:
            result['domain'] = [('id', 'in', pickings.ids)]
        elif len(pickings) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            form_view = [(res and res.id or False, 'form')]
            result['views'] = form_view + [(state, view) for state, view in result.get('views', []) if view != 'form']
            result['res_id'] = pickings.id
        return result

    def open_receipt(self):
        for rec in self:
            return {
                'name': _('Purchase Tracking Receipt'),
                'domain': [('partner_id', '=', rec.partner_id.id)],
                'view_type': 'form',
                'res_model': 'stock.picking',
                'view_id': False,
                'view_mode': 'tree,form',
                'type': 'ir.actions.act_window',
            }

    def get_receipt_count(self):
        for rec in self:
            count = self.env['stock.picking'].search_count([('partner_id', '=', rec.partner_id.id)])
            self.receipt_count = count

    receipt_count = fields.Integer(string='Receipt', compute='get_receipt_count')

    # def name_get(self):
    #     res = []
    #     for record in self:
    #         if record.purchase_id and record.name:
    #             name = '%s / %s' % (record.purchase_id.name, record.name)
    #             res.append((record.id, name))
    #         else:
    #             pass
    #     return res

    @api.depends('order_line_tracking.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line_tracking:
                line._compute_amount()
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            currency = order.currency_id or order.partner_id.property_purchase_currency_id or self.env.company.currency_id
            order.update({
                'amount_untaxed': currency.round(amount_untaxed),
                'amount_tax': currency.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('gs.purchase.tracking.sequence') or _('New')
        result = super(GsPurchaseTracking, self).create(vals)
        return result

    @api.model
    def _default_picking(self):
        picking = self.env['stock.picking'].search([('partner_id', '=', self.partner_id.id), ('state', '=', 'assigned')],limit=1)
        return picking.id

    @api.model
    def _default_picking_type(self):
        return self._get_picking_type(self.env.context.get('company_id') or self.env.company.id)

    @api.model
    def _get_picking_type(self, company_id):
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return picking_type[:1]

    @api.onchange('company_id')
    def _onchange_company_id(self):
        p_type = self.picking_type_id
        if not(p_type and p_type.code == 'incoming' and (p_type.warehouse_id.company_id == self.company_id or not p_type.warehouse_id)):
            self.picking_type_id = self._get_picking_type(self.company_id.id)

    # @api.onchange('purchase_id')
    # def _onchange_purchase_ids(self):
    #     for rec in self:
    #         if rec.purchase_id:
    #             for purchase in rec.purchase_id:
    #                 rec.partner_id = purchase.partner_id
    #                 rec.currency_id = purchase.currency_id
    #                 lines = [(5, 0, 0)]
    #                 for pro in purchase.order_line:
    #                     val = {
    #                         'product_id': pro.product_id.id if pro.product_id.id else False,
    #                         'name': pro.name if pro.name else False,
    #                         'currency_id': pro.currency_id.id if pro.currency_id.id else False,
    #                         'product_type': pro.product_type if pro.product_type else False,
    #                         'product_uom_category_id': pro.product_uom_category_id if pro.product_uom_category_id else False,
    #                         'sequence': pro.sequence if pro.sequence else False,
    #                         'date_planned': pro.date_planned if pro.date_planned else False,
    #                         'product_qty': pro.product_qty if pro.product_qty else False,
    #                         'product_uom': pro.product_uom.id if pro.product_uom.id else False,
    #                         'category_id': pro.category_id.id if pro.category_id.id else False,
    #                         'sh_is_secondary_unit': pro.sh_is_secondary_unit if pro.sh_is_secondary_unit else False,
    #                         'sh_sec_qty': pro.sh_sec_qty if pro.sh_sec_qty else False,
    #                         'sh_sec_uom': pro.sh_sec_uom.id if pro.sh_sec_uom.id else False,
    #                         'price_unit': pro.price_unit if pro.price_unit else False,
    #                         'taxes_id': pro.taxes_id.ids if pro.taxes_id.ids else False,
    #                         'price_subtotal': pro.price_subtotal if pro.price_subtotal else False,
    #                     }
    #                     lines.append((0, 0, val))
    #                     rec.order_line_tracking = lines

    def action_create_bill(self):
        for x in self:
            lines = [(5, 0, 0)]
            purchase_tracking = 0
            x.is_create_bill = False
            move_vals_list = []
            for pro in self.order_line_tracking:
                pro.under_shipment += pro.shipment
                pro.qty -= pro.shipment
                if pro.shipment_bill == 0:
                    pass
                else:
                    val = {
                        'product_id': pro.product_id.id if pro.product_id.id else False,
                        'name': pro.name if pro.name else False,
                        'price_unit': pro.price_unit if pro.price_unit else False,
                        'quantity': pro.shipment_bill if pro.shipment_bill else False,
                        'sh_is_secondary_unit': pro.sh_is_secondary_unit if pro.sh_is_secondary_unit else False,
                        'sh_sec_qty': pro.sh_sec_qty if pro.sh_sec_qty else False,
                        'sh_sec_uom': pro.sh_sec_uom.id if pro.sh_sec_uom.id else False,
                        'product_uom_id': pro.product_uom.id if pro.product_uom.id else False,
                        'analytic_account_id': pro.tracking_id.analytic_account_id.id if pro.tracking_id.analytic_account_id.id else False,
                        # 'analytic_tag_ids': [(6, 0, pro.tracking_id.analytic_tag_id.ids)],
                        'tax_ids': [(6, 0, pro.taxes_id.ids)],
                        'price_subtotal': pro.price_subtotal if pro.price_subtotal else False,

                    }
                    lines.append((0, 0, val))
                    purchase_tracking = lines
            if purchase_tracking:
                move_vals_list.append({
                    'move_type': 'in_invoice',
                    'partner_id': x.partner_id.id,
                    'invoice_date': x.date_planned,
                    'invoice_line_ids': purchase_tracking
                })
                invoice_id = self.env['account.move'].create(move_vals_list)
                x.invoice_id = [(4, invoice_id.id)]

    is_create_bill = fields.Boolean()

    def action_crate_receipt(self, date_order):
        lines = [(5, 0, 0)]
        purchase_tracking = 0
        self.is_create_bill = True
        for pro in self.order_line_tracking:
            pro.under_shipment += pro.shipment
            pro.qty -= pro.shipment
            pro.shipment_bill = 0
            if pro.shipment == 0:
                pass
            else:
                val = {
                    'product_id': pro.product_id.id if pro.product_id.id else False,
                    'name': pro.name if pro.name else False,
                    'company_id': pro.company_id.id if pro.company_id.id else False,
                    'product_type': pro.product_type if pro.product_type else False,
                    'date': pro.date_planned if pro.date_planned else False,
                    # 'date_deadline': pro.date_planned if pro.date_planned else False,
                    'product_uom_qty': pro.shipment if pro.shipment else False,
                    # 'product_qty': pro.product_qty if pro.product_qty else False,
                    'product_uom': pro.product_uom.id if pro.product_uom.id else False,
                    'sh_is_secondary_unit': pro.sh_is_secondary_unit if pro.sh_is_secondary_unit else False,
                    'sh_sec_qty': pro.sh_sec_qty if pro.sh_sec_qty else False,
                    'sh_sec_uom': pro.sh_sec_uom.id if pro.sh_sec_uom.id else False,
                    'location_id': pro.tracking_id.partner_id.property_stock_supplier.id,
                    'location_dest_id': pro.tracking_id.picking_type_id.default_location_dest_id.id,
                    'state': 'confirmed',

                }
                lines.append((0, 0, val))
                purchase_tracking = lines
                pro.shipment_bill = pro.shipment
                pro.shipment = 0
        if purchase_tracking:
            picking_vals = {
                'tracking_id': self.id,
                'partner_id': self.partner_id.id,
                'picking_type_id': self.picking_type_id.id,
                'company_id': self.company_id.id,
                'user_id': self.user_id.id,
                'origin': self.name,
                'move_type': 'direct',
                'scheduled_date': date_order,
                'date_deadline': self.date_planned,
                'location_id': self.partner_id.property_stock_supplier.id,
                'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                'move_ids_without_package': purchase_tracking if purchase_tracking else False,
            }
            self.env['stock.picking'].create(picking_vals)

    partner_id = fields.Many2one('res.partner', string='Vendor')
    name = fields.Char('Reference', required=True, copy=False, readonly=True,
                                          index=True, default=lambda self: _('New'))
    partner_ref = fields.Char('Vendor Reference',)
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.company.currency_id.id)
    date_order = fields.Datetime('Order Deadline', default=fields.Datetime.now)
    date_planned = fields.Datetime(string='Receipt Date',)
    order_line_tracking = fields.One2many('purchase.order.line.tracking', 'tracking_id', store=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company.id)
    tax_totals_json = fields.Binary(compute='_compute_tax_totals_json')
    user_id = fields.Many2one(
        'res.users', string='Purchase Representative', index=True, tracking=True,
        default=lambda self: self.env.user, check_company=True)
    origin = fields.Char('Source Document', copy=False,
        help="Reference of the document that generated this purchase order "
             "request (e.g. a sales order)")
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Terms', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    incoterm_id = fields.Many2one('account.incoterms', 'Incoterm', help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")
    purchase_id = fields.Many2one('purchase.order', string='Purchase')
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', tracking=True)
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')
    tax_country_id = fields.Many2one(
        comodel_name='res.country',
        compute='_compute_tax_country_id',
        compute_sudo=True,
        help="Technical field to filter the available taxes depending on the fiscal country and fiscal position.")
    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', required=True, default=_default_picking_type, domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
        help="This will determine operation type of incoming shipment")
    incoming_picking_count = fields.Integer("Incoming Shipment count", compute='_compute_incoming_picking_count')
    location_id = fields.Many2one('stock.location', 'Source Location',)
    location_dest_id = fields.Many2one('stock.location', 'Destination Location',)
    picking_id = fields.Many2one('stock.picking', 'Transfer',)
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('submit', 'Submit'),
            ('approved', 'Approved'),
            ('locked', 'Locked'),
            ('unlocked', 'Unlocked'),
            ('cancel', 'Cancelled'),
        ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    is_finish = fields.Boolean(copmpute='_compute_action_crate_receipt')
    invoice_id = fields.Many2many('account.move', string="Invoice", domain="[('move_type', '=', 'out_invoice')]")
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    # analytic_tag_id = fields.Many2one('account.analytic.tag', string='Analytic Tag')

    invoice_count = fields.Integer(compute='get_gs_invoice_count')

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

    city = fields.Char(string='City',)
    port = fields.Char(string='Port',)
    def open_gs_invoice(self):
        return {
            'name': _('Invoice'),
            'domain': [('id', 'in', self.invoice_id.ids)],
            'view_type': 'form',
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_gs_invoice_count(self):
        count = self.env['account.move'].search_count([('id', 'in', self.invoice_id.ids)])
        self.invoice_count = count

    def _compute_action_crate_receipt(self):
        for line in self.order_line_tracking:
            if line.product_qty == line.under_shipment:
                self.is_finish = True
            else:
                self.is_finish = False

    def _compute_incoming_picking_count(self):
        self._compute_action_crate_receipt()
        pickings = self.env['stock.picking'].search_count([('tracking_id', '=', self.id)])
        self.incoming_picking_count = pickings

    @api.depends('company_id.account_fiscal_country_id', 'fiscal_position_id.country_id', 'fiscal_position_id.foreign_vat')
    def _compute_tax_country_id(self):
        for record in self:
            if record.fiscal_position_id.foreign_vat:
                record.tax_country_id = record.fiscal_position_id.country_id
            else:
                record.tax_country_id = record.company_id.account_fiscal_country_id

    @api.depends('order_line_tracking.taxes_id', 'order_line_tracking.price_subtotal', 'amount_total', 'amount_untaxed')
    def _compute_tax_totals_json(self):
        # def compute_taxes(order_line_tracking):
        #     return order_line_tracking.taxes_id._origin.compute_all(**order_line_tracking._prepare_compute_all_values())
        #
        # account_move = self.env['account.move']
        # for order in self:
        #     tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(order.order_line_tracking, compute_taxes)
        #     tax_totals = account_move._get_tax_totals(order.partner_id, tax_lines_data, order.amount_total, order.amount_untaxed, order.currency_id)
        #     order.tax_totals_json = json.dumps(tax_totals)
        AccountTax = self.env['account.tax']
        for order in self:
            if not order.company_id:
                order.tax_totals_json = False
                continue
            order_lines = order.order_line_tracking.filtered(lambda x: not x.display_type)
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
            AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
            order.tax_totals_json = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.currency_id or order.company_id.currency_id,
                company=order.company_id,
            )


    is_cancel = fields.Boolean(compute="_get_default_cancel")
    is_draft = fields.Boolean(compute="_get_default_draft")
    is_approve = fields.Boolean(compute="_get_default_approve")
    is_submit = fields.Boolean(compute="_get_default_submit")
    is_crate_receipt = fields.Boolean(compute="_get_default_crate_receipt")
    is_create_bill_bol = fields.Boolean(compute="_get_default_crate_bill")
    is_lock_bol = fields.Boolean(compute="_get_default_lock")
    is_unlock_bol = fields.Boolean(compute="_get_default_unlock")

    def _get_default_submit(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search([('permission_type', '=', 'p_purchase_tracking')], limit=1)
            rec.is_submit = False
            if permission:
                if user in permission.submit_t_id.ids:
                    rec.is_submit = True

    def _get_default_crate_receipt(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search([('permission_type', '=', 'p_purchase_tracking')], limit=1)
            rec.is_crate_receipt = False
            if permission:
                if user in permission.create_receipt_t_id.ids:
                    rec.is_crate_receipt = True

    def _get_default_crate_bill(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search([('permission_type', '=', 'p_purchase_tracking')], limit=1)
            rec.is_create_bill_bol = False
            if permission:
                if user in permission.create_bill_t_id.ids:
                    rec.is_create_bill_bol = True
                    
    def _get_default_approve(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search([('permission_type', '=', 'p_purchase_tracking')], limit=1)
            rec.is_approve = False
            if permission:
                if user in permission.approve_t_id.ids:
                    rec.is_approve = True    
                    
    def _get_default_cancel(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search([('permission_type', '=', 'p_purchase_tracking')], limit=1)
            rec.is_cancel = False
            if permission:
                if user in permission.cancel_t_id.ids:
                    rec.is_cancel = True

    def _get_default_draft(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search([('permission_type', '=', 'p_purchase_tracking')], limit=1)
            rec.is_draft = False
            if permission:
                if user in permission.draft_t_id.ids:
                    rec.is_draft = True

    def _get_default_unlock(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_purchase_tracking')], limit=1)
            rec.is_unlock_bol = False
            if permission:
                if user in permission.unlock_t_id.ids:
                    rec.is_unlock_bol = True

    def _get_default_lock(self):
        for rec in self:
            user = rec.env.user.id
            permission = self.env['gs.purchase.tracking.permission'].search(
                [('permission_type', '=', 'p_purchase_tracking')], limit=1)
            rec.is_lock_bol = False
            if permission:
                if user in permission.lock_t_id.ids:
                    rec.is_lock_bol = True


class PurchaseOrderLineTracking(models.Model):
    _name = 'purchase.order.line.tracking'

    @api.onchange('partner_id', 'product_id')
    def domain_product_id(self):
        for rec in self:
            products = self.env['product.product'].search([('purchase_ok', '=', True)])
            list = []
            for product in products:
                for seller in product.seller_ids:
                    if rec.partner_id == seller.name:
                        list.append(product.id)
            return {'domain': {'product_id': [('id', 'in', list)]}}

    tracking_id = fields.Many2one('gs.purchase.tracking', string='Tracking Reference', index=True, required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', related='tracking_id.partner_id')
    product_id = fields.Many2one('product.product', string='Product', change_default=True)
    product_type = fields.Selection(related='product_id.type', readonly=True)
    name = fields.Text(string='Description')
    date_planned = fields.Datetime(string='Delivery Date', index=True, default=fields.Datetime.now,
        help="Delivery date expected from vendor. This date respectively defaults to vendor pricelist lead time then today's date.")
    sequence = fields.Integer(string='Sequence', default=10)
    product_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True)
    qty = fields.Float()
    sh_sec_qty = fields.Float("Secondary Qty",digits='Product Unit of Measure')
    sh_sec_uom = fields.Many2one("uom.uom", 'Secondary UOM')
    sh_is_secondary_unit = fields.Boolean("Related Sec Unit", related="product_id.sh_is_secondary_unit")
    category_id = fields.Many2one("uom.category", "Purchase UOM Category", related="product_uom.category_id")
    taxes_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]", related='product_id.uom_po_id')
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    price_unit = fields.Float(string='Unit Price', required=True, digits='Purchase Tracking Decimal 5 digits')

    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True, digits='Purchase Tracking Decimal 4 digits')
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True, digits='Purchase Tracking Decimal 2 digits')
    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=True)
    company_id = fields.Many2one('res.company', related='tracking_id.company_id', string='Company', store=True, readonly=True)
    currency_id = fields.Many2one(related='tracking_id.currency_id', store=True, string='Currency', readonly=True)
    location_id = fields.Many2one('stock.location', 'Source Location',)
    location_dest_id = fields.Many2one('stock.location', 'Destination Location',)
    shipment = fields.Float(string='Shipment',  digits='Product Unit of Measure')
    under_shipment = fields.Float(string='Under Shipment',  digits='Product Unit of Measure')
    shipment_bill = fields.Integer()
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

    qty_received = fields.Float("Received", compute='_compute_qty_received', digits='Product Unit of Measure')
    qty_invoiced = fields.Float(compute='_compute_qty_invoiced', string="Billed", digits='Product Unit of Measure')


    def _compute_qty_received(self):
        receipts = self.env['stock.picking'].search([('tracking_id', '=', self.tracking_id.id)])
        self.qty_received = 0
        qty_received = 0
        for receipt in receipts:
            if receipt.state == 'done':
                for line in receipt.move_ids_without_package:
                    qty_received += line.quantity_done
                self.qty_received = qty_received

    def _compute_qty_invoiced(self):
        self.qty_invoiced = 0
        qty_invoiced = 0
        for line1 in self.tracking_id.invoice_id:
            if line1.state == 'posted':
                for line2 in line1.invoice_line_ids:
                    qty_invoiced += line2.quantity
                self.qty_invoiced = qty_invoiced

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            if self.product_id.default_code and self.product_id.name and self.product_id.description_purchase:
                self.name = str('[' + self.product_id.default_code + ']' + self.product_id.name + ' ' + self.product_id.description_purchase)
            elif not self.product_id.description_purchase:
                self.name = str('[' + self.product_id.default_code + ']' + self.product_id.name)
            elif not self.product_id.default_code:
                self.name = str(self.product_id.name + ' ' + self.product_id.description_purchase)

    @api.onchange('product_qty')
    def onchange_product_qty(self):
        for rec in self:
            if rec.product_qty:
                rec.qty = rec.product_qty

    @api.onchange('shipment', 'product_qty', 'qty')
    def onchange_shipment(self):
        if self.shipment and self.product_qty and self.qty:
            if self.shipment > self.qty:
                raise ValidationError(_("Shipment More Than  Quantity"))

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
        # Hook method to returns the different argument values for the
        # compute_all method, due to the fact that discounts mechanism
        # is not implemented yet on the purchase orders.
        # This method should disappear as soon as this feature is
        # also introduced like in the sales module.
        self.ensure_one()
        return {
            'price_unit': self.price_unit,
            'currency': self.tracking_id.currency_id,
            'quantity': self.product_qty,
            'product': self.product_id,
            'partner': self.tracking_id.partner_id,
        }
