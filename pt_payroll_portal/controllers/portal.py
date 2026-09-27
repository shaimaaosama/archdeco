from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.osv.expression import OR
from collections import OrderedDict
from odoo.tools import date_utils, groupby as groupbyelem
from operator import itemgetter
from odoo.tools import consteq
from urllib.parse import quote

class PortalPayslipController(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        employee = request.env['res.users']._get_employee_from_user()
        if 'payslip_count' in counters:
            payslipCount = request.env['hr.payslip'].sudo().search_count([
                ('employee_id', '=', employee.id),
                ('state', '=', 'done'),
                ('portal_visible', '=', True)
            ])
            values['payslip_count'] = payslipCount or '0'
        return values

    def _payslip_check_access(self, payslip_id, access_token=None):
        """Check if user has access to the payslip."""
        payslip = request.env['hr.payslip'].sudo().browse(payslip_id)
        if not payslip:
            return False

        if access_token and payslip.access_token and consteq(payslip.access_token, access_token):
            return payslip

        if request.env.user.has_group('base.group_portal') or request.env.user.has_group('base.group_user'):
            employee = request.env['res.users']._get_employee_from_user()
            if employee and employee.id == payslip.employee_id.id and payslip.portal_visible:
                return payslip

        if request.env.user.has_group('pt_payroll_portal.group_hr_payroll_user'):
            return payslip

        return False

    @http.route(['/my/payslips', '/my/payslips/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_payslips(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='all', **kw):
        """Display payslips list."""
        values = self._prepare_portal_layout_values()

        employee = request.env['res.users']._get_employee_from_user()
        if not employee:
            return request.redirect('/my')

        HrPayslip = request.env['hr.payslip'].sudo()

        domain = [
            ('employee_id', '=', employee.id),
            ('state', '=', 'done'),
            ('portal_visible', '=', True)
        ]

        if date_begin and date_end:
            domain += [('date_from', '>=', date_begin), ('date_to', '<=', date_end)]

        if not sortby:
            sortby = 'date'
        order = 'date_from desc'

        if search and search_in:
            search_domain = []
            if search_in in ('name', 'all'):
                search_domain = [('name', 'ilike', search)]
            domain += search_domain

        payslip_count = HrPayslip.search_count(domain)

        pager = portal_pager(
            url="/my/payslips",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'search_in': search_in, 'search': search},
            total=payslip_count,
            page=page,
            step=self._items_per_page
        )
        payslips = HrPayslip.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'payslips': payslips,
            'page_name': 'payslips',
            'default_url': '/my/payslips',
            'pager': pager,
            'searchbar_sortings': {'date': {'label': _('Date'), 'order': 'date_from desc'}},
            'sortby': sortby,
            'search_in': search_in,
            'search': search,
        })

        return request.render("pt_payroll_portal.portal_my_payslips", values)

    @http.route(['/my/payslip/<int:payslip_id>'], type='http', auth="public", website=True)
    def portal_my_payslip_detail(self, payslip_id, access_token=None, **kw):
        """Display payslip detail."""
        try:
            payslip_sudo = self._payslip_check_access(payslip_id, access_token)
            if payslip_sudo.employee_id.user_id.id != request.uid:
                return request.redirect('/my')
            if not payslip_sudo:
                raise AccessError("Unauthorized access to payslip")
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = {
            'page_name': 'payslip',
            'payslip': payslip_sudo,
        }

        return request.render("pt_payroll_portal.portal_my_payslip", values)

    @http.route(['/my/payslip/<int:payslip_id>/download'], type='http', auth="public", website=True)
    def portal_my_payslip_download(self, payslip_id, access_token=None, **kw):
        """Download payslip PDF."""
        try:
            payslip_sudo = self._payslip_check_access(payslip_id, access_token)
            if not payslip_sudo:
                raise AccessError("Unauthorized access to payslip")
        except (AccessError, MissingError):
            return request.redirect('/my')

        try:
            report_ref = 'gs_hr_payroll_custom.pt_ar_action_report_payslip_hr_hr_ar'
            if not request.env.ref(report_ref, raise_if_not_found=False):
                report_ref = 'hr_payroll.action_report_payslip'
            pdf_content, report_type = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
                report_ref, [payslip_sudo.id]
            )
        except Exception as e:
            raise UserError(_("Error generating payslip PDF: %s") % str(e))

        filename = payslip_sudo.name or "payslip"
        filename_utf8 = quote(filename.encode('utf-8'))

        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition', "attachment; filename*=UTF-8''%s.pdf" % filename_utf8),
        ]

        return request.make_response(pdf_content, headers=pdfhttpheaders)
