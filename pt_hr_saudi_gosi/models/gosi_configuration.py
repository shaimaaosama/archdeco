from odoo import fields, api, models

from odoo.exceptions import UserError


class GosiSaudiConfig(models.Model):
    _name = 'gosi.config'
    _description = 'GOSI Configuration'

    name = fields.Char('Name', default='Gosi Salary Global Configuration')

    max_gosi_salary = fields.Float('Maximum Gosi Salary',default=45000)

    company_share_per = fields.Float('Company Share % (Saudi) اكثر من 50 سنة او اكثر 240 شهر', default=12.25)
    company_share_per_non = fields.Float('Company Share % (Non Saudi)', default=2.5)
    company_share_per_less_than_fifty_years = fields.Float('Company Share % (Saudi) اقل من 50 سنة او اقل 240 شهر', default=12.25)
    company_saudah_share_per = fields.Float(string="Company Share % سعوده")

    employee_share_per = fields.Float('Employee Share % (Saudi) اكثر من 50 سنة او اكثر 240 شهر', default=9.75)
    employee_share_per_non = fields.Float('Employee Share % (Non Saudi)', default=0.0)
    employee_share_per_less_than_fifty_years = fields.Float('Employee Share % (Saudi) اقل من 50 سنة او اقل 240 شهر', default=10.25)
    employee_saudah_share_per = fields.Float(string="Employee Share % سعوده")


    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if self.search_count([]) > 1:
            raise UserError("Sorry, You Can Only Create Just One Configuration For Now.")
        return records