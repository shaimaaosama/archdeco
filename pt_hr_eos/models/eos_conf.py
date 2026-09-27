from odoo import fields, models


class EosConf(models.Model):
    _name = "eos.conf"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Eos Conf"
    _rec_name = 'company_id'

    journal_id = fields.Many2one('account.journal')
    account_id = fields.Many2one('account.account', string="Account debit")
    account_credit_id = fields.Many2one('account.account', string="Account Credit")
    day_of_operation = fields.Integer(string="Day")
    company_id = fields.Many2one('res.company')
