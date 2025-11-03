# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields


class res_partner(models.Model):
    _inherit = 'res.partner'

    check_credit = fields.Boolean('Check Credit')
    credit_limit_on_hold = fields.Boolean('Credit limit on hold')
    credit_limit = fields.Float('Credit Limit')

    credit_limit_config_bool = fields.Boolean(compute='_compute_credit_limit_config')


    def _compute_credit_limit_config(self):
        for record in self:
           if self.env.user.has_group('gs_customer_credit_limit.credit_limit_config'):
               record.credit_limit_config_bool = True
           else:
               record.credit_limit_config_bool = False

