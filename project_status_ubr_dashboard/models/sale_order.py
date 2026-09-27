# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    boq_component_ids = fields.One2many(
        comodel_name="sale.order.boq.component",
        inverse_name="order_id",
        string="BOQ Components",
        copy=True,
    )

    total_expected_expense = fields.Float(compute="_compute_total_expected_expense",)

    @api.depends("order_line.unit_cost", "order_line.product_uom_qty", "order_line.display_type", )
    def _compute_total_expected_expense(self):
        for order in self:
            order.total_expected_expense = sum(
                line.unit_cost * line.product_uom_qty
                for line in order.order_line
                if not line.display_type
            )

    can_see_boq = fields.Boolean(compute="_compute_can_see_boq",)

    @api.depends_context("uid")
    def _compute_can_see_boq(self):
        permission = self.env["gs.sales.permission"].sudo().search([
            ("can_see_boq_user_ids", "in", self.env.user.id),
        ], limit=1)

        for order in self:
            order.can_see_boq = bool(permission)

    def action_confirm(self):
        required_branch_ids = self.env["gs.sales.permission"].sudo().search([]).mapped("boq_required_branch_ids").ids

        for order in self:
            if order.branch_id.id in required_branch_ids and not order.boq_component_ids:
                raise ValidationError(
                    _("You cannot confirm this Sales Order without adding BOQ components.")
                )

        return super().action_confirm()

    def _prepare_confirmation_values(self):
        values = super()._prepare_confirmation_values()
        values.pop("date_order", None)
        return values

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    component_cost = fields.Monetary(
        compute="_compute_component_cost_from_boq",
        currency_field="currency_id",
    )

    unit_cost = fields.Float()

    @api.depends(
        "product_id",
        "order_id.boq_component_ids.component_id",
        "order_id.boq_component_ids.total_cost",
    )
    def _compute_component_cost_from_boq(self):
        for line in self:
            if not line.order_id or not line.product_id or line.display_type:
                line.component_cost = 0.0
                continue

            components = line.order_id.boq_component_ids.filtered(
                lambda component:
                    component.component_id == line.product_id
            )

            line.component_cost = sum(
                components.mapped("total_cost")
            )

class SaleOrderBoqMaterialMaster(models.Model):
    _name = "sale.order.boq.material.master"
    _description = "BOQ Material"
    _order = "code, name, id"

    name = fields.Char(
        string="Material Name",
        required=True,
        translate=True,
    )

    code = fields.Char(
        string="Material Code",
        index=True,
    )

    default_unit_cost = fields.Float(
        string="Default Unit Cost",
        digits="Product Price",
        default=0.0,
    )

    active = fields.Boolean(
        string="Active",
        default=True,
    )

    note = fields.Text(
        string="Notes",
    )

    _sql_constraints = [
        (
            "boq_material_code_unique",
            "unique(code)",
            "The BOQ material code must be unique.",
        ),
    ]

    @api.depends("code", "name")
    def _compute_display_name(self):
        for material in self:
            if material.code:
                material.display_name = f"[{material.code}] {material.name}"
            else:
                material.display_name = material.name

    @api.constrains("default_unit_cost")
    def _check_default_unit_cost(self):
        for material in self:
            if material.default_unit_cost < 0:
                raise ValidationError(
                    "The default unit cost cannot be negative."
                )


class SaleOrderBoqComponent(models.Model):
    _name = "sale.order.boq.component"
    _description = "Sale Order BOQ Component"
    _order = "sequence, id"

    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )

    order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale Order",
        required=True,
        ondelete="cascade",
        index=True,
    )

    allowed_component_product_ids = fields.Many2many(
        comodel_name="product.product",
        string="Allowed Components",
        compute="_compute_allowed_component_product_ids",
    )

    component_id = fields.Many2one(
        comodel_name="product.product",
        string="Component",
        required=True,
        domain="[('id', 'in', allowed_component_product_ids)]",
    )

    quantity = fields.Float(
        string="Quantity",
        digits="Product Unit of Measure",
        compute="_compute_component_cost",
        store=True,
    )

    component_unit_cost = fields.Monetary(
        string="Unit Cost",
        compute="_compute_component_cost",
        store=True,
        currency_field="currency_id",
    )

    overhead_percentage = fields.Float(
        string="Overhead %",
        default=0.0,
    )

    materials_total_cost = fields.Monetary(
        string="Materials Cost",
        compute="_compute_component_cost",
        store=True,
        currency_field="currency_id",
    )

    overhead_amount = fields.Monetary(
        string="Overhead Amount",
        compute="_compute_component_cost",
        store=True,
        currency_field="currency_id",
    )

    total_cost = fields.Monetary(
        string="Total Cost",
        compute="_compute_component_cost",
        store=True,
        currency_field="currency_id",
    )

    material_line_ids = fields.One2many(
        comodel_name="sale.order.boq.material.line",
        inverse_name="component_id",
        string="Materials",
        copy=True,
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        related="order_id.currency_id",
        store=True,
        readonly=True,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        related="order_id.company_id",
        store=True,
        readonly=True,
    )

    @api.depends(
        "order_id.order_line.product_id",
        "order_id.order_line.display_type",
        "order_id.order_line.is_downpayment",
    )
    def _compute_allowed_component_product_ids(self):
        for component in self:
            component.allowed_component_product_ids = (
                component.order_id.order_line.filtered(
                    lambda line:
                        not line.display_type
                        and line.product_id
                        and not line.is_downpayment
                ).mapped("product_id")
            )

    @api.depends(
        "overhead_percentage",
        "material_line_ids.quantity",
        "material_line_ids.unit_cost",
        "material_line_ids.total_cost",
    )
    def _compute_component_cost(self):
        for component in self:
            quantity = sum(
                component.material_line_ids.mapped("quantity")
            )

            materials_total_cost = sum(
                component.material_line_ids.mapped("total_cost")
            )

            component_unit_cost = (
                materials_total_cost / quantity
                if quantity
                else 0.0
            )

            overhead_amount = (
                materials_total_cost
                * component.overhead_percentage
                / 100.0
            )

            component.quantity = quantity
            component.component_unit_cost = component_unit_cost
            component.materials_total_cost = materials_total_cost
            component.overhead_amount = overhead_amount
            component.total_cost = materials_total_cost + overhead_amount

    @api.constrains("component_id", "order_id")
    def _check_component_in_sale_order(self):
        for component in self:
            if not component.component_id or not component.order_id:
                continue

            order_products = component.order_id.order_line.filtered(
                lambda line:
                    not line.display_type
                    and line.product_id
                    and not line.is_downpayment
            ).mapped("product_id")

            if component.component_id not in order_products:
                raise ValidationError(
                    "The selected component must exist in the sale order lines."
                )

    @api.constrains("overhead_percentage")
    def _check_overhead_percentage(self):
        for component in self:
            if component.overhead_percentage < 0:
                raise ValidationError(
                    "The overhead percentage cannot be negative."
                )


class SaleOrderBoqMaterialLine(models.Model):
    _name = "sale.order.boq.material.line"
    _description = "Sale Order BOQ Material Line"
    _order = "sequence, id"

    sequence = fields.Integer( string="Sequence", default=10,)

    component_id = fields.Many2one( comodel_name="sale.order.boq.component", required=True, ondelete="cascade", index=True,)

    order_id = fields.Many2one( comodel_name="sale.order", string="Sale Order",  related="component_id.order_id",  store=True, readonly=True,)

    material_id = fields.Many2one( comodel_name="sale.order.boq.material.master", required=True, domain="[('active', '=', True)]",)

    description = fields.Char()

    quantity = fields.Float( digits="Product Unit of Measure", required=True, default=1.0,)

    unit_cost = fields.Monetary( required=True, default=0.0, currency_field="currency_id",)

    total_cost = fields.Monetary( compute="_compute_total_cost", store=True, currency_field="currency_id",)

    notes = fields.Char()

    currency_id = fields.Many2one( comodel_name="res.currency", related="component_id.currency_id", store=True, readonly=True, )

    company_id = fields.Many2one( comodel_name="res.company", string="Company", related="component_id.company_id", store=True, readonly=True, )

    @api.depends( "quantity", "unit_cost",)
    def _compute_total_cost(self):
        for material_line in self:
            material_line.total_cost = (
                material_line.quantity
                * material_line.unit_cost
            )

    @api.onchange("material_id")
    def _onchange_material_id(self):
        for material_line in self:
            if not material_line.material_id:
                material_line.unit_cost = 0.0
                continue

            material_line.unit_cost = (
                material_line.material_id.default_unit_cost
            )

    @api.constrains("quantity")
    def _check_quantity(self):
        for material_line in self:
            if material_line.quantity <= 0:
                raise ValidationError(
                    "The material quantity must be greater than zero."
                )

    @api.constrains("unit_cost")
    def _check_unit_cost(self):
        for material_line in self:
            if material_line.unit_cost < 0:
                raise ValidationError(
                    "The material unit cost cannot be negative."
                )

class gsSalesPermission(models.Model):
    _inherit = "gs.sales.permission"

    can_see_boq_user_ids = fields.Many2many(comodel_name="res.users", relation="gs_sales_permission_can_see_boq_user_rel", column1="permission_id", column2="user_id", string="Can See BOQ", domain=[("share", "=", False)],)
    boq_required_branch_ids = fields.Many2many(comodel_name="res.branch", relation="gs_sales_permission_boq_branch_rel", column1="permission_id", column2="branch_id", string="BOQ Required Branches",)

