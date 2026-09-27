from odoo import models, fields


class PaymentCompany(models.Model):
    _name = "payment.company"
    _description = "Payment Company"
    _rec_name = "company_id_number"


    company_id_number = fields.Char(
        string="Company ID Number",
        required=True,
    )