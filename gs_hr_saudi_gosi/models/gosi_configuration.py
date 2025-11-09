from odoo import fields, api, models, _

from odoo.exceptions import UserError

class GosiSaudiConfig(models.Model):
    _name = 'gosi.config'

    name = fields.Char('Name',default='Gosi Salary Global Configuration')

    max_gosi_salary = fields.Float('Maximum Gosi Salary',default=45000)

    company_share_per = fields.Float('Company Share % (Saudi)', default=12.5)
    company_share_per_non = fields.Float('Company Share % (Non Saudi)', default=2.5)

    employee_share_per = fields.Float('Employee Share % (Saudi)', default=10.0)
    employee_share_per_non = fields.Float('Employee Share % (Non Saudi)', default=0.0)


    @api.model
    def create(self, vals):
        res = super(GosiSaudiConfig, self).create(vals)
        configs = res.env['gosi.config'].search([])
        if len(configs) > 1:
            raise UserError("Sorry, You Can Only Create Just One Configuration For Now.")
        return res