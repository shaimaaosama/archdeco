from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    sale_persone_id = fields.Many2one(comodel_name='res.users',  string='collection representative', domain="['|',('active','=', False),('active','!=', False)]", default=lambda self: self.env.user)


class AccountPaymentRegisterInherit(models.TransientModel):
    _inherit = 'account.payment.register'

    sale_persone_payment_id = fields.Many2one(comodel_name='res.users', required=True,
                                              string='collection representative')

    def _create_payment_vals_from_wizard(self,batch_result):
        payment_vals = super(AccountPaymentRegisterInherit, self)._create_payment_vals_from_wizard(batch_result)

        payment_vals['sale_persone_id'] = self.sale_persone_payment_id.id

        return payment_vals
