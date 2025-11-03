# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import timedelta
import itertools
from operator import itemgetter
import operator
from datetime import datetime
#========For Excel========
import xlwt
from xlwt import easyxf
import base64
from io import BytesIO


class dev_stock_card(models.TransientModel):
    _name ='dev.stock.card'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required="1")
    location_id = fields.Many2one('stock.location', string='Location', domain="[('usage','=','internal')]", required="1")
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    filter_by = fields.Selection([('product','Product'),('category', 'Product Category')],string='Filter By', default='product')
    category_id = fields.Many2one('product.category',string='Category')
    product_ids = fields.Many2many('product.product',string='Products')
    company_id = fields.Many2one('res.company', required="1", default = lambda self:self.env.user.company_id)
    excel_file = fields.Binary('Excel File')

    # domain on Many2one location_id
    @api.onchange('warehouse_id')
    def _compute_location_id_domain(self):
        print('_compute_location_id_domain')
        loc = []
        domain = []
        for rec in self:
            if rec.warehouse_id:
                    loc.append(rec.warehouse_id.lot_stock_id.id)
            # print('loc', loc)
        return {'domain': {'location_id': [('id', 'in', loc)]}}

    def get_product_ids(self):
        product_pool = self.env['product.product']
        if self.filter_by and self.filter_by == 'product':
            return self.product_ids.ids
        elif self.filter_by and self.filter_by == 'category':
            product_ids = product_pool.search([('type', '=', 'product'), ('categ_id', 'child_of', self.category_id.id)])
            return product_ids.ids
        else:
            product_ids = product_pool.search([('type', '=', 'product')])
            return product_ids.ids

    def in_lines(self,product_ids):
        start_date = str(self.start_date) + ' 00:00:00'
        # print('start_date===', start_date)
        end_date = str(self.end_date) + ' 23:59:59'
        # print('end_date===', end_date)
        state = ('draft', 'cancel')
        query = """select DATE(sm.date) as date, sm.origin as origin, sm.reference as ref, sm.location_id as locc, sm.location_dest_id as locd, pt.name as product,\
                  sm.product_uom_qty as in_qty, sm.product_uom as m_uom, pt.uom_po_id as p_uom, pp.id as product_id from stock_move as sm \
                  JOIN product_product as pp ON pp.id = sm.product_id \
                  JOIN product_template as pt ON pp.product_tmpl_id = pt.id \
                  where sm.date >= %s and sm.date <= %s \
                  and sm.location_dest_id = %s and sm.product_id in %s \
                  and sm.state not in %s and sm.company_id = %s
                  """

        params = (start_date, end_date, self.location_id.id, tuple(product_ids), state, self.company_id.id)
        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        for res in result:
            f_date = ' '
            if res.get('date'):
                data_date = datetime.strptime(str(res.get('date')),'%Y-%m-%d')
                f_date = data_date.strftime('%d-%m-%Y')
            if res.get('m_uom') and res.get('p_uom') and res.get('in_qty'):
                if res.get('m_uom') != res.get('p_uom'):
                    move_uom = self.env['uom.uom'].browse(res.get('m_uom'))
                    product_uom = self.env['uom.uom'].browse(res.get('p_uom'))
                    qty = move_uom._compute_quantity(res.get('in_qty'), product_uom)
                    res.update({
                        'in_qty':qty,
                        'date':f_date,
                    })
            res.update({
                'out_qty':0.0,
                'date':f_date,
            })
        return result

    def out_lines(self, product_ids):
        state = ('draft', 'cancel')
        start_date = str(self.start_date) + ' 00:00:00'
        end_date = str(self.end_date) + ' 23:59:59'
        # print('start_date==out=', start_date)
        # print('end_date==in=', end_date)
        move_type = 'outgoing'
        m_type = ''
        if self.location_id:
            m_type = 'and sm.location_id = %s'
        query = """select DATE(sm.date) as date, sm.origin as origin, sm.reference as ref, sm.location_id as locc, sm.location_dest_id as locd, pt.name as product,\
                      sm.product_uom_qty as out_qty,sm.product_uom as m_uom, pt.uom_id as p_uom, pp.id as product_id \
                      from stock_move as sm JOIN product_product as pp ON pp.id = sm.product_id \
                      JOIN product_template as pt ON pp.product_tmpl_id = pt.id \
                      where sm.date >= %s and sm.date <= %s \
                      and sm.location_id = %s and sm.product_id in %s \
                      and sm.state not in %s and sm.company_id = %s
                      """
        params = (start_date, end_date, self.location_id.id, tuple(product_ids), state, self.company_id.id)
        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        for res in result:
            f_date = ' '
            if res.get('date'):
                data_date = datetime.strptime(str(res.get('date')),'%Y-%m-%d')
                f_date = data_date.strftime('%d-%m-%Y')
            if res.get('m_uom') and res.get('p_uom') and res.get('out_qty'):
                if res.get('m_uom') != res.get('p_uom'):
                    move_uom = self.env['uom.uom'].browse(res.get('m_uom'))
                    product_uom = self.env['uom.uom'].browse(res.get('p_uom'))
                    qty = move_uom._compute_quantity(res.get('out_qty'), product_uom)
                    res.update({
                        'out_qty':qty,
                        'date':f_date,
                    })
            res.update({
                'in_qty': 0.0,
                'date':f_date,
            })
        return result
        
    def get_lines(self):
        product_ids = self.get_product_ids()
        result = []
        if product_ids:
            in_lines = self.in_lines(product_ids)
            # print('in_lines==', in_lines)
            out_lines = self.out_lines(product_ids)
            # print('out_lines==', out_lines)
            lst = in_lines + out_lines
            # print('lst==', lst)

            # Python Sort given list of dictionaries by date
            # printing initial list
            # print("initial list : ", str(lst))
            # code to sort list on date
            lst.sort(key=lambda x: x['date'])
            # printing final list
            # print("result", str(lst))

            new_lst = sorted(lst, key=itemgetter('product'))
            # print('new_lst==', new_lst)
            groups = itertools.groupby(new_lst, key=operator.itemgetter('product'))
            # print('groups==', groups)
            result = [{'product': k, 'values': [x for x in v]} for k, v in groups]
            # print('result==', result)
            for res in result:
                l_data = res.get('values')
                new_lst = sorted(l_data, key=itemgetter('date'))
                res['values'] = new_lst

        return result
        
    # def print_pdf(self):
    #     data={}
    #     data['form'] = self.read()[0]
    #     return self.env.ref('gl_stock_card_report.print_stock_card_report').report_action(self, data=None)
    
    def get_date(self):
#        s_date = datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S').date()
        start_date = self.start_date.strftime('%m-%d-%Y')
#        e_date = datetime.strptime(str(self.end_date), '%Y-%m-%d %H:%M:%S').date()
        end_date = self.end_date.strftime('%m-%d-%Y')        
        
        data = {'start_date':start_date , 'end_date':end_date}
        return data
    
    def get_style(self):
        main_header_style = easyxf('font:height 300;'
                                   'align: horiz center;font: color black; font:bold True;'
                                   "borders: top thin,left thin,right thin,bottom thin")
                                   
        header_style = easyxf('font:height 200;pattern: pattern solid, fore_color gray25;'
                              'align: horiz right;font: color black; font:bold True;'
                              "borders: top thin,left thin,right thin,bottom thin")
        
        left_header_style = easyxf('font:height 200;pattern: pattern solid, fore_color gray25;'
                              'align: horiz left;font: color black; font:bold True;'
                              "borders: top thin,left thin,right thin,bottom thin")
        
        
        text_left = easyxf('font:height 200; align: horiz left;')
        
        text_right = easyxf('font:height 200; align: horiz right;', num_format_str='0.00')
        
        text_left_bold = easyxf('font:height 200; align: horiz right;font:bold True;')
        
        text_right_bold = easyxf('font:height 200; align: horiz right;font:bold True;', num_format_str='0.00') 
        text_center = easyxf('font:height 200; align: horiz center;'
                             "borders: top thin,left thin,right thin,bottom thin")  
        
        return [main_header_style, left_header_style,header_style, text_left, text_right, text_left_bold, text_right_bold, text_center]

    def in_lines_for_opening(self,product_ids):
        start_date = '2010-01-01' + ' 00:00:00'
        # print('start_date===', start_date)
        end_date = str(self.start_date) + ' 00:00:00'
        # print('end_date===', end_date)
        # print('self.start_date===', self.start_date)
        state = ('draft', 'cancel')
        query = """select DATE(sm.date) as date, sm.origin as origin, sm.reference as ref, sm.location_id as locc, sm.location_dest_id as locd, pt.name as product,\
                  sm.product_uom_qty as in_qty, sm.product_uom as m_uom, pt.uom_po_id as p_uom, pp.id as product_id from stock_move as sm \
                  JOIN product_product as pp ON pp.id = sm.product_id \
                  JOIN product_template as pt ON pp.product_tmpl_id = pt.id \
                  where sm.date >= %s and sm.date <= %s \
                  and sm.location_dest_id = %s and sm.product_id in %s \
                  and sm.state not in %s and sm.company_id = %s
                  """

        params = (start_date, end_date, self.location_id.id, tuple(product_ids), state, self.company_id.id)
        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        for res in result:
            f_date = ' '
            if res.get('date'):
                data_date = datetime.strptime(str(res.get('date')),'%Y-%m-%d')
                f_date = data_date.strftime('%d-%m-%Y')
            if res.get('m_uom') and res.get('p_uom') and res.get('in_qty'):
                if res.get('m_uom') != res.get('p_uom'):
                    move_uom = self.env['uom.uom'].browse(res.get('m_uom'))
                    product_uom = self.env['uom.uom'].browse(res.get('p_uom'))
                    qty = move_uom._compute_quantity(res.get('in_qty'), product_uom)
                    res.update({
                        'in_qty':qty,
                        'date':f_date,
                    })
            res.update({
                'out_qty':0.0,
                'date':f_date,
            })
        return result

    def out_lines_for_opening(self, product_ids):
        state = ('draft', 'cancel')
        start_date = '2010-01-01' + ' 00:00:00'
        # print('start_date=out==', start_date)
        end_date = str(self.start_date) + ' 00:00:00'
        # print('end_date==out=', end_date)
        # print('self.start_date==out=', self.start_date)
        move_type = 'outgoing'
        m_type = ''
        if self.location_id:
            m_type = 'and sm.location_id = %s'
        query = """select DATE(sm.date) as date, sm.origin as origin, sm.reference as ref, sm.location_id as locc, sm.location_dest_id as locd, pt.name as product,\
                      sm.product_uom_qty as out_qty,sm.product_uom as m_uom, pt.uom_id as p_uom, pp.id as product_id \
                      from stock_move as sm JOIN product_product as pp ON pp.id = sm.product_id \
                      JOIN product_template as pt ON pp.product_tmpl_id = pt.id \
                      where sm.date >= %s and sm.date <= %s \
                      and sm.location_id = %s and sm.product_id in %s \
                      and sm.state not in %s and sm.company_id = %s
                      """
        params = (start_date, end_date, self.location_id.id, tuple(product_ids), state, self.company_id.id)
        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        for res in result:
            f_date = ' '
            if res.get('date'):
                data_date = datetime.strptime(str(res.get('date')),'%Y-%m-%d')
                f_date = data_date.strftime('%d-%m-%Y')
            if res.get('m_uom') and res.get('p_uom') and res.get('out_qty'):
                if res.get('m_uom') != res.get('p_uom'):
                    move_uom = self.env['uom.uom'].browse(res.get('m_uom'))
                    product_uom = self.env['uom.uom'].browse(res.get('p_uom'))
                    qty = move_uom._compute_quantity(res.get('out_qty'), product_uom)
                    res.update({
                        'out_qty':qty,
                        'date':f_date,
                    })
            res.update({
                'in_qty': 0.0,
                'date':f_date,
            })
        return result

    def get_lines_for_opening(self):
        product_ids = self.get_product_ids()
        result = []
        if product_ids:
            in_lines = self.in_lines_for_opening(product_ids)
            # print('in_lines==', in_lines)
            out_lines = self.out_lines_for_opening(product_ids)
            # print('out_lines==', out_lines)
            lst = in_lines + out_lines
            # print('lst==', lst)
            # Python Sort given list of dictionaries by date
            # printing initial list
            # print("initial list : ", str(lst))
            # code to sort list on date
            lst.sort(key=lambda x: x['date'])
            # printing final list
            # print("result", str(lst))
            new_lst = sorted(lst, key=itemgetter('product'))
            # print('new_lst==', new_lst)
            groups = itertools.groupby(new_lst, key=operator.itemgetter('product'))
            # print('groups==', groups)
            result = [{'product': k, 'values': [x for x in v]} for k, v in groups]
            # print('result==', result)
            for res in result:
                l_data = res.get('values')
                new_lst = sorted(l_data, key=itemgetter('date'))
                res['values'] = new_lst
        return result

    def get_opening_quantity(self, product):
        print('get_opening_quantity')
        lines = self.get_lines_for_opening()
        balance = 0
        t_in_qty = t_out_qty = 0
        if lines:
            for line in lines:
                for val in line.get('values'):
                    balance += val.get('in_qty') - val.get('out_qty')
                    t_in_qty += val.get('in_qty')
                    t_out_qty += val.get('out_qty')
        # print('balance=====', balance)
        qty = balance
        # print('t_in_qty=====', t_in_qty)
        # print('t_out_qty=====', t_out_qty)

        # product = self.env['product.product'].browse(product)
        # print('product==', product)
        # #        date = datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S')
        # date = self.start_date - timedelta(days=1)
        # print('date==', date)
        # date = date.strftime('%Y-%m-%d')
        # qty = product.with_context(to_date=date, location_id=self.location_id.id).qty_available
        # # qwee = product.with_context(location_id=self.location_id.id).qty_available
        # # print('qwee==', qwee)
        # # print('self.product.qty_available.location_id.id.id==', product.qty_available)
        # # print('self.product.qty_available.location_id.id.id==', product.qty_available.location_id.id)
        # # print('self.location_id.id==', self.location_id.id)
        # # current_pro = self.env['stock.quant'].search([('product_id', '=', product.id),
        # #                                               ('location_id', '=', self.location_id.id)])
        # # print('current_pro==', current_pro)
        # # print('current_pro==', current_pro.quantity)
        # # if current_pro:
        # #     qty = current_pro.quantity
        # #     print('qty==', qty)
        # # else:
        # #     qty = 0
        return qty

    def create_excel_header(self,worksheet,main_header_style,text_left,text_center,left_header_style,text_right,header_style):
        worksheet.write_merge(0, 1, 1, 3, 'Stock Card', main_header_style)
        row = 2
        col = 1
        start_date = datetime.strptime(str(self.start_date), '%Y-%m-%d')
        start_date = datetime.strftime(start_date, "%d-%m-%Y ")
        end_date = datetime.strptime(str(self.end_date), '%Y-%m-%d')
        end_date = datetime.strftime(end_date, "%d-%m-%Y ")
        date = start_date + ' To '+ end_date
        worksheet.write_merge(row,row, col, col+2, date, text_center)
        row += 2
        worksheet.write(row, 0, 'Location', left_header_style)
        worksheet.write_merge(row,row, 1, 2, self.location_id.display_name, text_left)
        row+=1
        worksheet.write(row, 0, 'Company', left_header_style)
        worksheet.write_merge(row,row, 1, 2, self.company_id.name, text_left)
        row+=2
        worksheet.write(row, 0, 'Date', left_header_style)
        worksheet.write(row,1, 'Partner', left_header_style)
        worksheet.write(row,2, 'From', left_header_style)
        worksheet.write(row,3, 'TO', left_header_style)
        worksheet.write(row,4, 'Type', left_header_style)
        worksheet.write(row,5, 'Ref', left_header_style)
        worksheet.write(row,6, 'In Qty', header_style)
        worksheet.write(row,7, 'Out Qty', header_style)
        worksheet.write(row,8, 'Balance', header_style)
        worksheet.write(row,9, 'Uom', left_header_style)
        lines = self.get_lines()
        # print('lines==', lines)
        # print('location==', self.location_id)
        # print('date==', self.end_date)
        p_group_style = easyxf('font:height 200;pattern: pattern solid, fore_color ivory;'
                              'align: horiz left;font: color black; font:bold True;'
                              "borders: top thin,left thin,right thin,bottom thin")
        group_style = easyxf('font:height 200;pattern: pattern solid, fore_color ice_blue;'
                              'align: horiz left;font: color black; font:bold True;'
                              "borders: top thin,left thin,right thin,bottom thin")
        group_style_right = easyxf('font:height 200;pattern: pattern solid, fore_color ice_blue;'
                              'align: horiz right;font: color black; font:bold True;'
                              "borders: top thin,left thin,right thin,bottom thin", num_format_str='0.00')
        row+=1
        all_lines_ids = []
        if lines:
            for line in lines:
                worksheet.write_merge(row,row, 0,4, line.get('product'), p_group_style)
                row += 1
                count = 0
                balance = 0
                t_in_qty = t_out_qty = 0
                for val in line.get('values'):
                    # print('idsss lines==', val.get('product_id'))
                    all_lines_ids.append(val.get('product_id'))
                    # print('all_lines_ids', all_lines_ids)
                    count += 1
                    if count == 1:
                        # worksheet.write_merge(row,row,0,2, 'Opening Quantity', group_style)
                        op_qty = self.get_opening_quantity(val.get('product_id'))
                        balance = op_qty
                        # empty cell in excel
                        # worksheet.write(row,3, '', group_style_right)
                        worksheet.write(row,8, op_qty, group_style_right)
                        row+=1
                    balance += val.get('in_qty') - val.get('out_qty')
                    t_in_qty += val.get('in_qty')
                    t_out_qty += val.get('out_qty')
                    worksheet.write(row,0, val.get('date'), text_left)
                    uom_c = self.env['uom.uom'].search([('id', '=', val.get('m_uom'))])
                    if uom_c:
                        worksheet.write(row, 9, uom_c.name, text_left)
                    partner_c = self.env['stock.picking'].search([('name', '=', val.get('ref'))])
                    # print('partner_c==', partner_c )
                    # print('ref=', val.get('ref') )
                    # print('partner_c====', partner_c.partner_id)
                    # print('partner_c.picking_type_id.sequence_code====', partner_c.picking_type_id.sequence_code)
                    if partner_c:
                        worksheet.write(row,1, partner_c.partner_id.name, text_left)

                    if val.get('ref') != 'Product Quantity Updated':
                        scrap_type = val.get('ref')
                        sc = scrap_type.split('/')[0]
                        if sc == 'SP':
                            worksheet.write(row, 4, 'Scrap', text_left)
                        else:
                            worksheet.write(row, 4, partner_c.picking_type_id.sequence_code, text_left)
                        # worksheet.write(row, 2, self.location_id.display_name, text_left)
                        to_c = self.env['stock.move.line'].search([('reference', '=', val.get('ref'))])
                        location_loc = self.env['stock.location'].search([('id', '=', val.get('locc'))])
                        if location_loc:
                            worksheet.write(row, 2, location_loc.display_name, text_left)
                        # print('to_c==', to_c )
                        # print('val.ge====', val.get('ref'))
                        # print('locc==', val.get('locc'))
                        # print('locd==', val.get('locd'))
                        # print('to_c.location_dest_id.display_name==', to_c.location_dest_id.display_name )
                        if to_c:
                            # print('=======', val.get('ref'))
                            # print('=======len=', len(to_c))
                            # print('=======id=', to_c.id)
                            # ____________________________________________
                            # all_ids = []
                            # if len(to_c) > 1:
                            #     i = 0
                            #     all_ids.append(to_c.ids)
                            #     # print('iddddssssss=', to_c.ids)
                            #     print('all_ids=', all_ids)
                            #     pass
                            #     for e in all_ids:
                            #         if i <= len(to_c):
                            #             print('e[i]', e[i])
                            #             print('i==', i)
                            #             final_loc = self.env['stock.move.line'].search([('id', '=', e[i])])
                            #             worksheet.write(row, 3, final_loc.location_dest_id.display_name, text_right)
                            #         i += 1
                            # ____________________________________________
                            # if len(to_c) > 1:
                                # row += 1
                                # i = 0
                                # num_of_len = len(to_c)
                                # for e in to_c.ids:
                                #     if i <= num_of_len:
                                #         print('i===', i)
                                #         final_loc = self.env['stock.move.line'].search([('id', '=', to_c.ids[i])])
                                #         worksheet.write(row, 3, final_loc.location_dest_id.display_name, text_right)
                                #         row += 1
                                #         i += 1
                                #         # print('i=1=', i)
                                # row += 1
                            worksheet.write(row,3, to_c[0].location_dest_id.display_name, text_left)
                    else:
                        worksheet.write(row, 4, 'Adjustments', text_left)
                        location_pro_update = self.env['stock.location'].search([('id', '=', val.get('locc'))])
                        location_pro_update_locd = self.env['stock.location'].search([('id', '=', val.get('locd'))])
                        # print('location_pro_update==', location_pro_update )
                        worksheet.write(row, 2, location_pro_update.display_name, text_left)
                        worksheet.write(row, 3, location_pro_update_locd.display_name, text_left)
                        # print('locc222==', val.get('locc'))
                        # print('locc222==', val.get('locd'))
                    worksheet.write(row,5, val.get('origin') or val.get('ref'), text_left)
                    worksheet.write(row,6, val.get('in_qty'), text_right)
                    worksheet.write(row,7, val.get('out_qty'), text_right)
                    worksheet.write(row,8, balance, text_right)
                    row+=1
                worksheet.write_merge(row,row,0,5, 'Total', group_style_right)
                worksheet.write(row,6, t_in_qty, group_style_right)
                worksheet.write(row,7, t_out_qty, group_style_right)
                worksheet.write(row,8, balance, group_style_right)
                row+=2
            all_ids_in_self_products = []
            # print('all_lines_ids==', all_lines_ids)
            for p in self.product_ids:
                all_ids_in_self_products.append(p.id)
                # print('idsss', p.id , 'val' , val.get('product_id'))
                # print('all_ids_in_self_products', all_ids_in_self_products)
            # print('all_ids_in_self_products==', all_ids_in_self_products)
            last_ids = [item for item in all_ids_in_self_products if item not in all_lines_ids]
            # print('last_ids', last_ids)
            # print('last_ids len==', len(last_ids))
            len_ids = len(last_ids)
            i = 0
            row += 1
            if last_ids:
                worksheet.write(row, 4, 'all of this products have not any moves in this days', text_left)
            for dd in last_ids:
                if i <= len_ids:
                    all_pro_not_in_date = self.env['stock.quant'].search([('location_id', '=', self.location_id.id),
                                                                          ('product_id', '=', last_ids[i])])
                    # print('last_ids[i]==', last_ids[i])
                    # print('all_pro_not_in_date', all_pro_not_in_date)
                    worksheet.write_merge(row, row, 0, 3, all_pro_not_in_date.product_id.name, p_group_style)
                    row += 1
                    count = 0
                    balance = 0
                    t_in_qty = t_out_qty = 0
                    # for val in partner_c:
                    count += 1
                    if count == 1:
                        worksheet.write(row, 2, all_pro_not_in_date.location_id.display_name, text_left)
                        worksheet.write(row, 8, all_pro_not_in_date.quantity, group_style_right)
                        row += 1
                    i += 1
                    # print('i===', i)
                # row += 1
                # return worksheet, row
            row += 1
            return worksheet, row
        else:
            # print('there no lines')
            # print('location==', self.location_id)
            # print('date==', self.end_date)
            # print('date==', self.product_ids)
            # print('product_ids==', self.product_ids.default_code)
            if self.product_ids:
                for pp in self.product_ids:
                    if self.product_ids:
                        partner_c = self.env['stock.quant'].search([('location_id', '=', self.location_id.id),
                                                                    ('product_id', '=', pp.id)])
                        # print('partner_c=1=', partner_c)
                    else:
                        partner_c = self.env['stock.quant'].search([('location_id', '=', self.location_id.id)])
                        # print('partner_c=2=', partner_c)
                    # print('quantity==', partner_c.quantity)
                    # print('inventory_date==', partner_c.inventory_date)
                    for pro in partner_c:
                        worksheet.write_merge(row, row, 0, 4, pro.product_id.name, p_group_style)
                    row += 1
                    count = 0
                    balance = 0
                    t_in_qty = t_out_qty = 0
                    for val in partner_c:
                        count += 1
                        if count == 1:
                            worksheet.write(row, 2, val.location_id.display_name, text_left)
                            worksheet.write(row, 8, val.quantity, group_style_right)
                            row += 1
                row += 1
                return worksheet, row
            if self.filter_by == 'category':
                partner_c = self.env['stock.quant'].search([('location_id', '=', self.location_id.id)])
                # print('partner_c=2===', partner_c)
                for pro in partner_c:
                    worksheet.write_merge(row, row, 0, 4, pro.product_id.name, p_group_style)
                    worksheet.write(row, 8, pro.quantity, group_style_right)
                    row += 1
                    count = 0
                    balance = 0
                    t_in_qty = t_out_qty = 0
                    for val in partner_c:
                        count += 1
                        if count == 1:
                            worksheet.write(row, 2, val.location_id.display_name, text_left)
                            row += 1
            row += 1
            return worksheet, row

    def action_generate_excel(self):
        #====================================
        # Style of Excel Sheet 
        excel_style = self.get_style()
        main_header_style = excel_style[0]
        left_header_style = excel_style[1]
        header_style = excel_style[2]
        text_left = excel_style[3]
        text_right = excel_style[4]
        text_left_bold = excel_style[5]
        text_right_bold = excel_style[6]
        text_center = excel_style[7]
        # ====================================
        workbook = xlwt.Workbook()
        filename = 'Stock Card Report.xls'
        worksheet = workbook.add_sheet('Stock Card', cell_overwrite_ok=True)
        for i in range(0,10):
            worksheet.col(i).width = 150 * 30
        worksheet,row = self.create_excel_header(worksheet,main_header_style,text_left,text_center,left_header_style,text_right,header_style)
        #download Excel File
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        excel_file = base64.encodestring(fp.read())
        fp.close()
        self.write({'excel_file': excel_file})
        if self.excel_file:
            active_id = self.ids[0]
            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/?model=dev.stock.card&download=true&field=excel_file&id=%s&filename=%s' % (
                    active_id, filename),
                'target': 'new',
            }
