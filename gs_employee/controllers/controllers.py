# -*- coding: utf-8 -*-
# from odoo import http


# class GsEmployee(http.Controller):
#     @http.route('/gs_employee/gs_employee/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/gs_employee/gs_employee/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('gs_employee.listing', {
#             'root': '/gs_employee/gs_employee',
#             'objects': http.request.env['gs_employee.gs_employee'].search([]),
#         })

#     @http.route('/gs_employee/gs_employee/objects/<model("gs_employee.gs_employee"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('gs_employee.object', {
#             'object': obj
#         })
