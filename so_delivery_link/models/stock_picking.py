from odoo import fields, models, api

class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    analytic_account_id = fields.Many2one("account.analytic.account")
    required_saleorder = fields.Boolean(related="picking_type_id.required_saleorder")
    required_analytic_account = fields.Boolean(related="picking_type_id.required_analytic_account")

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

    def button_validate(self):
        super().button_validate()
        for rec in self:
            if rec.analytic_account_id and rec.move_ids:
                for stock_move in rec.move_ids:
                    for account_move in stock_move.account_move_ids:
                        for account_move_line in account_move.line_ids:
                            account_move_line.analytic_distribution = {str(rec.analytic_account_id.id): 100.0}

class StockPickingInherit(models.Model):
    _inherit = 'stock.picking.type'

    required_saleorder = fields.Boolean()
    required_analytic_account = fields.Boolean()