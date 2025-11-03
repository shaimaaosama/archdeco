# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Jupical Technologies(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models
from datetime import datetime
from num2words import num2words



class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'
    price_basis = fields.Char(string=None)
    offer_validity= fields.Char(string=None)
    work_period = fields.Char(string=None)

    product_detials = fields.One2many(comodel_name='product.info',inverse_name='so_id')
    project_location = fields.Char(string=None)
    project = fields.Char(string=None)
    matrial = fields.Char(string=None)
    install = fields.Char(string=None)

    payment_terms = fields.Text(string=None)
    bank_detials = fields.Text(string=None)
    special_conditions = fields.Text(string=None)
    approval_rs_user_id = fields.Many2one("res.users",)

    def compute_amount_in_word(self,amount):
        if self.env.user.lang == 'en_US':
            num_word = str(self.currency_id.amount_to_text(amount)) + ' only'
            return num_word
        elif self.env.user.lang == 'ar_001':
            num_word = num2words(amount, to='currency', lang=self.env.user.lang)
            num_word = str(num_word) + ' فقط'
            return num_word

    def so_revision_quote(self):
        res = super(SaleOrderInherit, self).so_revision_quote()
        self.approval_rs_user_id = self.env.user.id
        return res


class Product(models.Model):
    _name= 'product.name'
    name = fields.Char(string='Name')

class ProductDeitails(models.Model):
    _name = 'product.info'
    prodcut_id = fields.Many2one('product.name',string='Product')
    brand= fields.Char(string='Brand')
    so_id = fields.Many2one(comodel_name='sale.order',string='So_id')
