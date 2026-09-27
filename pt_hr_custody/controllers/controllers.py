# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request

class HrManagementSystem(http.Controller):

    @http.route(['/request_review/<id>'], type='http', auth="public", website=True)
    def request_review(self, **kw):
        request_id = int(kw['id'])
        values = request.env['hr.custody'].sudo().search([('id', '=', request_id)])
        value = {
            'values': values,
        }
        return request.render("gs_hr_custody.request_review", value)

    @http.route('/request_approve', type='http', auth='public',website=True, csrf=False)
    def action_request_approve(self, *args, **post):
        request_id = int(post.get('hr_custody'))
        request_obj = http.request.env['hr.custody'].sudo().search([('id', '=', request_id)])

        if request_obj:
            request_obj.renew_approve()
            return http.request.render('gs_hr_custody.submit')

    @http.route('/request_refuse', type='http', auth='public',website=True, csrf=False)
    def action_request_refuse(self, *args, **post):
        request_id = int(post.get('hr_custody'))
        request_obj = http.request.env['hr.custody'].sudo().search([('id', '=', request_id)])

        if request_obj:
            request_obj.reject_request()
            return http.request.render('gs_hr_custody.submit')









