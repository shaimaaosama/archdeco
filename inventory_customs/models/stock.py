from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockPickingInherit(models.Model):
    _inherit = "stock.picking"

    analytic_account_id = fields.Many2one(comodel_name="account.analytic.account", string="Analytic Account",)
    required_saleorder = fields.Boolean(compute="compute_required_so_analytic",)
    required_analytic_account = fields.Boolean(compute="compute_required_so_analytic",)

    def _set_return_analytic_account(self):
        for rec in self:
            if rec.analytic_account_id:
                continue

            original_picking = rec.move_ids.mapped("origin_returned_move_id.picking_id")[:1]

            if original_picking and original_picking.analytic_account_id:
                rec.analytic_account_id = original_picking.analytic_account_id
                continue

            if rec.sale_id and rec.sale_id.analytic_account_id:
                rec.analytic_account_id = rec.sale_id.analytic_account_id

    def button_validate(self):
        self._set_return_analytic_account()

        for rec in self:
            if rec.sale_id.analytic_account_id and rec.sale_id.analytic_account_id != rec.analytic_account_id:
                raise ValidationError(
                    _("Picking analytic account must match the analytic account of the related Sale Order.")
                )

            if rec.required_analytic_account and not rec.analytic_account_id:
                raise ValidationError(
                    _("Please select an analytic account before validating the transfer.")
                )

        return super().button_validate()

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        if self.partner_id:
            self.sale_id = False
            self.origin = False

    @api.onchange("sale_id")
    def onchange_sale_id(self):
        self.analytic_account_id = False

        if self.sale_id:
            self.analytic_account_id = self.sale_id.analytic_account_id
            self.origin = self.sale_id.name

    @api.depends("picking_type_id", "location_dest_id",)
    def compute_required_so_analytic(self):
        for rec in self:
            rec.required_saleorder = False
            rec.required_analytic_account = False

            if not rec.picking_type_id or not rec.location_dest_id:
                continue

            same_destination = (
                rec.picking_type_id.default_location_dest_id
                and rec.picking_type_id.default_location_dest_id == rec.location_dest_id
            )

            if rec.picking_type_id.required_saleorder and same_destination:
                rec.required_saleorder = True

            if rec.picking_type_id.required_analytic_account and same_destination:
                rec.required_analytic_account = True


class StockPickingTypeInherit(models.Model):
    _inherit = "stock.picking.type"

    required_saleorder = fields.Boolean(string="Required Sale Order",)
    required_analytic_account = fields.Boolean(string="Required Analytic Account",)


class StockMoveInherit(models.Model):
    _inherit = "stock.move"

    def _get_transfer_analytic_account(self):
        self.ensure_one()

        analytic_account = self.picking_id.analytic_account_id

        if not analytic_account and self.origin_returned_move_id:
            analytic_account = self.origin_returned_move_id.picking_id.analytic_account_id

        if not analytic_account and self.purchase_line_id:
            purchase_order = self.purchase_line_id.order_id

            if "analytic_account_id" in purchase_order._fields:
                analytic_account = purchase_order.analytic_account_id

        if not analytic_account and self.sale_line_id:
            analytic_account = self.sale_line_id.order_id.analytic_account_id

        if not analytic_account and self.group_id.sale_id:
            analytic_account = self.group_id.sale_id.analytic_account_id

        return analytic_account

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id, svl_id, description):
        account_move_lines = super()._prepare_account_move_line(
            qty,
            cost,
            credit_account_id,
            debit_account_id,
            svl_id,
            description,
        )

        self.ensure_one()

        analytic_account = self._get_transfer_analytic_account()

        if not analytic_account:
            return account_move_lines

        analytic_distribution = {str(analytic_account.id): 100.0}

        for command in account_move_lines:
            line_vals = False

            if isinstance(command, dict):
                line_vals = command
            elif isinstance(command, (list, tuple)) and len(command) >= 3 and isinstance(command[2], dict):
                line_vals = command[2]

            if not line_vals:
                continue

            line_vals["analytic_distribution"] = analytic_distribution

        return account_move_lines

    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()

        sale = self.sale_line_id.order_id or self.group_id.sale_id

        if sale and sale.analytic_account_id:
            vals["analytic_account_id"] = sale.analytic_account_id.id
        elif self.picking_id.analytic_account_id:
            vals["analytic_account_id"] = self.picking_id.analytic_account_id.id
        elif self.origin_returned_move_id.picking_id.analytic_account_id:
            vals["analytic_account_id"] = self.origin_returned_move_id.picking_id.analytic_account_id.id

        return vals