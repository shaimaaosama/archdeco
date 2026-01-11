from odoo import models, fields, api



class AccountMove(models.Model):
    _inherit = "account.move"


    def action_post(self):
        res = super().action_post()
        if self.origin_payment_id:
            self.origin_payment_id.action_post()
        return res