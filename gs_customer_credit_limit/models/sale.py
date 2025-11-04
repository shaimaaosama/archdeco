# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import datetime


class sale_order(models.Model):
    _inherit = 'sale.order'

    exceeded_amount = fields.Float('Exceeded Amount')
    t_or_f = fields.Boolean(compute='_compute_t_or_f', store=True)

    @api.depends('partner_id', 'state')
    def _compute_t_or_f(self):
        for rec in self:
            rec.t_or_f = False
            t_overdue = 0
            today_date = fields.Date.today()
            if rec.partner_id:
                if rec.partner_id.check_credit:
                    search_inv = self.env['account.move'].search([('partner_id', '=', rec.partner_id.id),
                                                                  ('payment_state', '!=', 'paid')])
                    if search_inv:
                        for m in search_inv:
                            if m.invoice_date_due:
                                if m.invoice_date_due <= today_date:
                                    t_overdue += m.amount_residual
                        if t_overdue >= 0.01 and rec.state == 'draft':
                            rec.t_or_f = True
                        else:
                            rec.t_or_f = False
                return rec.t_or_f

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('credit_limit', 'Credit limit'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        partner_id = self.partner_id
        today_date = fields.Date.today()
        t_overdue = 0
        if self.partner_id.parent_id:
            partner_id = self.partner_id.parent_id
        if partner_id:
            search_inv = self.env['account.move'].search([('partner_id', '=', partner_id.id),
                                                          ('payment_state', '!=', 'paid')])
            # print('search_inv', search_inv)
            for rec in search_inv:
                if rec.invoice_date_due:
                    # print('invoice_date_due', rec.invoice_date_due), print('today_date', today_date)
                    # print('rec.amount_residual', rec.amount_residual)
                    if rec.invoice_date_due <= today_date:
                        t_overdue += rec.amount_residual
                    #     print('t_overdue', t_overdue)
                    # print('t_overdue===', t_overdue)
            if partner_id.check_credit:
                if t_overdue >= 0.01:
                    msg = "Customer '" + partner_id.name + "' is on credit limit hold.( Total Overdue =" + str(
                        t_overdue) + ')'
                    return {'warning':
                                {'title': 'Credit Limit On Hold', 'message': msg
                                 }
                            }
        if partner_id:
            if partner_id.credit_limit_on_hold:
                msg = "Customer '" + partner_id.name + "' is on credit limit hold."
                return {'warning':
                            {'title': 'Credit Limit On Hold', 'message': msg
                             }
                        }
            if partner_id.check_credit:
                if partner_id.total_invoiced >= partner_id.credit_limit:
                    # print('====', partner_id.total_invoiced)
                    msg = "Customer '" + partner_id.name + "' is on credit limit hold."
                    return {'warning':
                                {'title': 'Credit Limit On Hold', 'message': msg
                                 }
                            }

    def action_sale_ok(self):
        partner_id = self.partner_id
        t_overdue = 0
        today_date = fields.Date.today()
        if partner_id:
            search_inv = self.env['account.move'].search([('partner_id', '=', partner_id.id),
                                                          ('payment_state', '!=', 'paid')])
            for rec in search_inv:
                if rec.invoice_date_due:
                    if rec.invoice_date_due <= today_date:
                        t_overdue += rec.amount_residual
            # for rec in self:
            #     print('self.t_or_f', self.t_or_f)
            #     rec.t_or_f = True
            #     print('self.t_or_f', self.t_or_f)
            # if t_overdue >= 0.01:
            #     raise ValidationError(_('Credit Limit On Hold For This Customer.'))
            # msg = "Customer '" + partner_id.name + "' is on credit limit hold.( Total Overdue ="+ str(t_overdue)+ ')'
            # return {'warning':
            #             {'title': 'Credit Limit On Hold', 'message': msg
            #              }
            #         }
        if self.partner_id.parent_id:
            partner_id = self.partner_id.parent_id
        partner_ids = [partner_id.id]
        for partner in partner_id.child_ids:
            partner_ids.append(partner.id)
        if partner_id.check_credit:
            domain = [
                ('order_id.partner_id', 'in', partner_ids),
                ('order_id.state', 'in', ['sale', 'credit_limit', 'done'])]
            order_lines = self.env['sale.order.line'].search(domain)
            order = []
            to_invoice_amount = 0.0
            for line in order_lines:
                not_invoiced = line.product_uom_qty - line.qty_invoiced
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_id.compute_all(
                    price, line.order_id.currency_id,
                    not_invoiced,
                    product=line.product_id, partner=line.order_id.partner_id)
                if line.order_id.id not in order:
                    if line.order_id.invoice_ids:
                        for inv in line.order_id.invoice_ids:
                            if inv.state == 'draft':
                                order.append(line.order_id.id)
                                break
                    else:
                        order.append(line.order_id.id)

                to_invoice_amount += taxes['total_included']

            domain = [
                ('move_id.partner_id', 'in', partner_ids),
                ('move_id.state', '=', 'draft'),
                ('sale_line_ids', '!=', False)]
            draft_invoice_lines = self.env['account.move.line'].search(domain)
            for line in draft_invoice_lines:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_ids.compute_all(
                    price, line.move_id.currency_id,
                    line.quantity,
                    product=line.product_id, partner=line.move_id.partner_id)
                to_invoice_amount += taxes['total_included']

            # We sum from all the invoices lines that are in draft and not linked
            # to a sale order
            domain = [
                ('move_id.partner_id', 'in', partner_ids),
                ('move_id.state', '=', 'draft'),
                ('sale_line_ids', '=', False)]
            draft_invoice_lines = self.env['account.move.line'].search(domain)
            draft_invoice_lines_amount = 0.0
            invoice = []
            for line in draft_invoice_lines:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_ids.compute_all(
                    price, line.move_id.currency_id,
                    line.quantity,
                    product=line.product_id, partner=line.move_id.partner_id)
                draft_invoice_lines_amount += taxes['total_included']
                if line.move_id.id not in invoice:
                    invoice.append(line.move_id.id)

            draft_invoice_lines_amount = "{:.2f}".format(draft_invoice_lines_amount)
            to_invoice_amount = "{:.2f}".format(to_invoice_amount)
            draft_invoice_lines_amount = float(draft_invoice_lines_amount)
            to_invoice_amount = float(to_invoice_amount)
            available_credit = partner_id.credit_limit - partner_id.credit - to_invoice_amount - draft_invoice_lines_amount

            if self.amount_total > available_credit:
                imd = self.env['ir.model.data'].sudo()
                exceeded_amount = (
                            to_invoice_amount + draft_invoice_lines_amount + partner_id.credit + self.amount_total)
                # - partner_id.credit_limit
                exceeded_amount = "{:.2f}".format(exceeded_amount)
                exceeded_amount = float(exceeded_amount)
                vals_wiz = {
                    'partner_id': partner_id.id,
                    'sale_orders': str(len(order)) + ' Sale Order Worth : ' + str(to_invoice_amount),
                    'invoices': str(len(invoice)) + ' Draft Invoice worth : ' + str(draft_invoice_lines_amount),
                    'current_sale': self.amount_total or 0.0,
                    'exceeded_amount': exceeded_amount,
                    'credit': partner_id.credit,
                    'credit_limit_on_hold': partner_id.credit_limit_on_hold,
                    'order_id': self.id,
                }
                wiz_id = self.env['customer.limit.wizard'].create(vals_wiz)
                # action = imd.xmlid_to_object('dev_customer_credit_limit.action_customer_limit_wizard')
                action = self.env["ir.actions.actions"]._for_xml_id(
                    'gs_customer_credit_limit.action_customer_limit_wizard')
                # form_view_id = imd.xmlid_to_res_id('dev_customer_credit_limit.view_customer_limit_wizard_form')
                form_view_id = self.env.ref('gs_customer_credit_limit.view_customer_limit_wizard_form').id
                # action['context'] = {
                #     'name': self.name,
                #     # 'help': help,
                #     # 'type': self.type,
                #     'views': [(form_view_id, 'form')],
                #     'view_id': form_view_id,
                #     'target': 'new',
                #     # 'context': self.context,
                #     'res_model': 'customer.limit.wizard',
                #     'res_id':wiz_id.id,
                #     }
                # return action['context']
                return {
                    'name': self.name,
                    # 'help': help,
                    # 'type': self.type,
                    'type': 'ir.actions.act_window',
                    'views': [(form_view_id, 'form')],
                    'view_id': form_view_id,
                    # 'target': self.target,
                    'target': 'new',
                    # 'res_model': self.res_model,
                    'res_model': 'customer.limit.wizard',
                    'res_id': wiz_id.id,
                }
            else:
                self.action_confirm()
        else:
            self.action_confirm()
        return True

    def _make_url(self, model='sale.order'):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url', default='http://localhost:8069')
        if base_url:
            base_url += '/web/login?db=%s&login=%s&key=%s#id=%s&model=%s' % (self._cr.dbname, '', '', self.id, model)
        return base_url

    def send_mail_approve_credit_limit(self):
        # this two lines worked on V14
        # manager_group_id = self.env['ir.model.data'].get_object_reference('gs_customer_credit_limit', 'credit_limit_config_on_hold')[1]
        # browse_group = self.env['res.groups'].browse(manager_group_id)
        users_g = self.env['res.users'].search(
            [('groups_id', 'in', [self.env.ref('gs_customer_credit_limit.credit_limit_config_on_hold').id])])
        partner_id = self.partner_id
        if self.partner_id.parent_id:
            partner_id = self.partner_id.parent_id
        url = self._make_url('sale.order')
        subject = str(self.name) + '-' + 'Require to Credit Limit Approval'
        # for user in browse_group.users:
        for user in users_g:
            partner = user.partner_id
            body = '''
                        <b>Dear ''' " %s</b>," % (partner.name) + '''
                        <p> A Sale Order ''' "<b><i>%s</i></b>" % self.name + '''  for customer ''' "<b><i>%s</i></b>" % partner_id.name + ''' require your Credit Limit Approval.</p>
                        <p>You can access sale order from  below url <br/>
                        ''' "%s" % url + ''' </p>

                        <p><b>Regards,</b> <br/>
                        ''' "<b><i>%s</i></b>" % self.user_id.name + ''' </p>
                        '''

            mail_values = {
                'email_from': self.user_id.email,
                'email_to': partner.email,
                'subject': subject,
                'body_html': body,
                'state': 'outgoing',
            }
            mail_id = self.env['mail.mail'].create(mail_values)
            mail_id.send(True)

    def set_credit_limit_state_also_if_has_due(self):
        # order_id = self.env['sale.order'].browse(self._context.get('active_id'))
        for order_id in self:
            order_id.state = 'credit_limit'
            order_id.exceeded_amount = self.exceeded_amount
            order_id.send_mail_approve_credit_limit()
            print('send notification')
            users_g = self.env['res.users'].search(
                [('groups_id', 'in', [self.env.ref('gs_customer_credit_limit.credit_limit_config_on_hold').id])])
            for user in users_g:
                # partner = user.partner_id
                self.sudo().make_activity(user.id)
        # partner_id = self.partner_id
        # if partner_id.parent_id:
        #     partner_id= partner_id.parent_id
        # partner_id.credit_limit_on_hold = self.credit_limit_on_hold
        return True

    def make_activity(self, manager):
        user_ids = []
        user_ids.append(manager)
        now = fields.datetime.now()
        date_deadline = now.date()
        if self:
            activ_list = []
            if user_ids:
                for rec in user_ids:
                    actv_id = self.sudo().activity_schedule(
                        'mail.mail_activity_data_todo', date_deadline,
                        note=_(
                            '<a>Task </a> for <a>Confirm</a>') % (
                             ),
                        user_id=rec,
                        res_id=self.id,
                        summary=_("Request ... Approve")
                    )
                    activ_list.append(actv_id.id)

    def make_activity_done(self):
        activity_ids = self.env['mail.activity'].sudo().search([('res_id', '=', self.id)])
        print(activity_ids)
        if activity_ids:
            for act in activity_ids:
                act.sudo().action_done()

    def action_cancel(self):
        res = super(sale_order, self).action_cancel()
        self.sudo().make_activity_done()
        return res

    def action_confirm(self):
        res = super(sale_order, self).action_confirm()
        self.sudo().make_activity_done()
        return res
