from datetime import datetime, time

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PurchaseExcelReportWizard(models.TransientModel):
    _name = "purchase.excel.report.wizard"
    _description = "Purchase Excel Report"

    date_from = fields.Date(string="Date From", required=True, default=fields.Date.context_today)
    date_to = fields.Date(string="Date To", required=True, default=fields.Date.context_today)
    company_ids = fields.Many2many(comodel_name="res.company", string="Companies", required=True, default=lambda self: self.env.companies)
    available_vendor_ids = fields.Many2many(comodel_name="res.partner", compute="_compute_available_vendor_ids")
    branch_ids = fields.Many2many(comodel_name="res.branch", string="Branches")
    partner_ids = fields.Many2many(comodel_name="res.partner", string="Vendors", domain="[('id', 'in', available_vendor_ids)]")
    purchase_order_ids = fields.Many2many(comodel_name="purchase.order", string="Purchase Orders", domain="[('company_id', 'in', company_ids)]")
    include_cancelled_bills = fields.Boolean(string="Include Cancelled Bills", default=False)

    @api.depends("company_ids",)
    def _compute_available_vendor_ids(self):
        PurchaseOrder = self.env["purchase.order"]

        for wizard in self:
            domain = []

            if wizard.company_ids:
                domain.append(("company_id", "in", wizard.company_ids.ids))

            purchase_orders = PurchaseOrder.search(domain)
            wizard.available_vendor_ids = purchase_orders.mapped("partner_id")

    @api.onchange("company_ids",)
    def _onchange_company_ids(self):
        allowed_vendors = self.available_vendor_ids
        allowed_purchase_orders = self.purchase_order_ids.filtered(lambda order: order.company_id in self.company_ids)

        self.partner_ids = self.partner_ids & allowed_vendors
        self.purchase_order_ids = allowed_purchase_orders

        return {
            "domain": {
                "partner_ids": [("id", "in", allowed_vendors.ids)],
                "purchase_order_ids": [("company_id", "in", self.company_ids.ids)],
            }
        }

    @api.onchange("partner_ids",)
    def _onchange_partner_ids(self):
        domain = [("company_id", "in", self.company_ids.ids)]

        if self.partner_ids:
            domain.append(("partner_id", "in", self.partner_ids.ids))

        allowed_purchase_orders = self.env["purchase.order"].search(domain)
        self.purchase_order_ids = self.purchase_order_ids & allowed_purchase_orders

        return {
            "domain": {
                "purchase_order_ids": domain,
            }
        }

    def action_export_xlsx(self):
        self.ensure_one()

        if self.date_from > self.date_to:
            raise ValidationError(_("Date From cannot be later than Date To."))

        date_from_datetime = datetime.combine(self.date_from, time.min)
        date_to_datetime = datetime.combine(self.date_to, time.max)

        data = {
            "wizard_id": self.id,
            "date_from": fields.Datetime.to_string(date_from_datetime),
            "date_to": fields.Datetime.to_string(date_to_datetime),
            "company_ids": self.company_ids.ids,
            "branch_ids": self.branch_ids.ids,
            "partner_ids": self.partner_ids.ids,
            "purchase_order_ids": self.purchase_order_ids.ids,
            "include_cancelled_bills": self.include_cancelled_bills,
        }

        return self.env.ref("inventory_customs.action_purchase_excel_xlsx_report").report_action(self, data=data)