# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductBrand(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one('product.brand', string='Brand')

    @api.onchange('name')
    def domain_location_ids(self):
        product_brands = self.env['product.brand'].search([])
        product_brand = []
        user1 = self.env.user.id
        for u in product_brands:
            for user in u.gs_user_ids:
                if user1 == user.id:
                    product_brand.append(u.id)
        return {'domain': {'brand_id': [('id', 'in', product_brand)]}}


class BrandProduct(models.Model):
    _name = 'product.brand'

    name = fields.Char(String="Name")
    brand_image = fields.Binary()
    member_ids = fields.One2many('product.template', 'brand_id', domain="[('brand_id','=',False)]")
    product_count = fields.Char(String='Product Count', compute='get_count_products', store=True)
    gs_user_ids = fields.Many2many('res.users', 'gs_user_ids01', 'gs_user_ids001', 'gs_user_ids0001', string="User")

    @api.depends('member_ids')
    def get_count_products(self):
        for rec in self:
            rec.product_count = len(rec.member_ids)
        # self.product_count = len(self.member_ids)


class BrandReportStock(models.Model):
    _inherit = 'stock.quant'

    brand_id = fields.Many2one(related='product_id.brand_id',
                               string='Brand', store=True, readonly=True)


class BrandPivotInvoicing(models.Model):
    _inherit = "account.invoice.report"

    brand_id = fields.Many2one('product.brand', string='Brand')

    @api.model
    def _select(self):
        select_str = super(BrandPivotInvoicing, self)._select()
        # find the marker
        marker = 'template.categ_id'
        idx = select_str.find(marker)
        if idx == -1:
            # fallback: log warning

            return select_str
        # find the comma after the marker alias
        # we assume something like: "template.categ_id                                           AS product_categ_id,"
        # So find the comma after the alias
        comma_pos = select_str.find(',', idx)
        if comma_pos == -1:
            # fallback
            return select_str
        # insert our field after the comma
        insertion = " template.brand_id as brand_id,"
        return select_str[:comma_pos + 1] + insertion + select_str[comma_pos + 1:]

    @api.model
    def _group_by(self):
        group_by_str = super(BrandPivotInvoicing, self)._group_by()
        return group_by_str + ", template.brand_id"


class PurchaseBrandPivot(models.Model):
    _inherit = 'purchase.report'

    brand_id = fields.Many2one('product.brand', string='Brand')

    def _select(self):
        res = super(PurchaseBrandPivot, self)._select()
        query = res.split('t.categ_id as category_id,', 1)
        rese = query[0] + 't.categ_id as category_id,t.brand_id as brand_id,' + query[1]
        return rese

    def _group_by(self):
        res = super(PurchaseBrandPivot, self)._group_by()
        query = res.split('t.categ_id,', 1)
        res = query[0] + 't.categ_id,t.brand_id,' + query[1]
        print(res)
        return res


class BrandPivot(models.Model):
    _inherit = 'sale.report'

    brand_id = fields.Many2one('product.brand', string='Brand')

    # def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
    #     fields['brand_id'] = ", t.brand_id as brand_id"
    #     groupby += ', t.brand_id'
    #     return super(BrandPivot, self)._query(with_clause, fields, groupby, from_clause)

    def _select_additional_fields(self):
        res = super()._select_additional_fields()

        res['brand_id'] = "t.brand_id"
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += """ ,t.brand_id"""
        return res

