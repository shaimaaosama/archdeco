from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from collections import OrderedDict
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.tools import date_utils, groupby as groupbyelem
from operator import itemgetter

from odoo.osv.expression import OR
# from odoo.addons.portal.controllers.mail import _message_post_helper

class EmployeeTimeoffPortal(CustomerPortal):

    def _prepare_portal_holiday_types(self, employee):
        hr_leave_types = request.env['hr.leave.type'].sudo().search([
            ('company_id', 'in', [employee.company_id.id, False]),
            '|',
            ('requires_allocation', '=', 'no'),
            ('has_valid_allocation', '=', True),
        ]).with_context({'employee_id': employee.id if employee else False})

        holiday_types = []
        for leave_type in hr_leave_types:
            display_name = leave_type.name
            if leave_type.requires_allocation != 'no' and not leave_type.hide_leave_counts:
                remaining = "%g" % (leave_type.virtual_remaining_leaves or 0.0)
                maximum = "%g" % (leave_type.max_leaves or 0.0)
                display_name = _('%(name)s (%(remaining)s من %(maximum)s متبقي)') % {
                    'name': leave_type.name,
                    'remaining': remaining,
                    'maximum': maximum,
                }
            holiday_types.append({
                'id': leave_type.id,
                'display_name': display_name,
            })
        return holiday_types
    
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        employee = request.env['hr.employee'].search([('user_id', '=', request.env.user.id)],limit=1)
        leave_count = request.env['hr.leave'].search_count([('employee_id', '=', employee and employee.id or False)])
        if 'leave_count' in counters:               
            values['leave_count'] = leave_count or '0'
        return values
    
    @http.route(['/my/leaves', '/my/leaves/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_leaves(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='all', groupby='none', **kw):        
        values = self._prepare_portal_layout_values()
        employee = request.env['hr.employee'].search([('user_id', '=', request.env.user.id)],limit=1)
        user = request.env.user
        HrLeave = request.env['hr.leave']
        
        domain = [
            ('employee_id', '=', employee and employee.id or False),
        ]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
        }
        
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'confirm': {'label': _('To Approve'), 'domain': [('state', '=', 'confirm')]},
            'refuse': {'label': _('Refused'), 'domain': [('state', '=', 'refuse')]},
            'validate1': {'label': _('Second Approval'), 'domain': [('state', '=', 'validate1')]},
            'validate': {'label': _('Approved'), 'domain': [('state', '=', 'validate')]},
        }
        
        searchbar_inputs = {
            'time_off_type': {'input': 'time_off_type', 'label': _('Search in Time Off Type')},
            'description': {'input': 'description', 'label': _('Search in description')},
            'start_date': {'input': 'start_date', 'label': _('Search in Start Date')},
            'end_date': {'input': 'end_date', 'label': _('Search in End Date')},
            'no_of_days': {'input': 'no_of_days', 'label': _('Search in No of days')},
            'status': {'input': 'status', 'label': _('Search in status')},            
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'time_off_type': {'input': 'time_off_type', 'label': _('Time Off Type')},
        }
        
        # default sortby value
        if not sortby:
            sortby = 'date'        
        order = searchbar_sortings[sortby]['order']
        
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        
        # search
        if search and search_in:
            search_domain = []
            if search_in in ('time_off_type', 'all'):
                search_domain = OR([search_domain, [('holiday_status_id.name', 'ilike', search)]])
            if search_in in ('description', 'all'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('start_date', 'all'):
                search_domain = OR([search_domain, [('request_date_from', 'ilike', search)]])
            if search_in in ('end_date', 'all'):
                search_domain = OR([search_domain, [('request_date_to', 'ilike', search)]])
            if search_in in ('no_of_days', 'all'):
                search_domain = OR([search_domain, [('number_of_days', 'ilike', search)]])
            if search_in in ('status', 'all'):
                search_domain = OR([search_domain, [('state', 'ilike', search)]])
            domain += search_domain
        
        # count for pager
        leave_count = HrLeave.search_count(domain)
        
        # make pager
        pager = portal_pager(
            url="/my/leaves",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'groupby': groupby, 'search_in': search_in, 'search': search},
            total=leave_count,
            page=page,
            step=self._items_per_page
        )    
        
        # default group by value
        if groupby == 'time_off_type':
            order = "holiday_status_id, %s" % order
        leaves = HrLeave.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        if groupby == 'none':
            grouped_leaves = []
            if leaves:
                grouped_leaves = [leaves]
        else:
            grouped_leaves = [HrLeave.sudo().concat(*g) for k, g in groupbyelem(leaves, itemgetter('holiday_status_id'))]
        
        values.update({
            'holiday_types': self._prepare_portal_holiday_types(employee)
        })
        
        values.update({
            'leaves': leaves,
            'date': date_begin,
            'date_end': date_end,
            'grouped_leaves': grouped_leaves,
            'page_name': 'leave',
            'default_url': '/my/leaves',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
            'sortby': sortby,
            'groupby': groupby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("pt_timeoff_portal.portal_my_leaves", values)
        
    @http.route(['/my/leave/<int:leave_id>'], type='http', auth="public", website=True)
    def portal_my_leave(self, leave_id, access_token=None, message=False, **kw):
        try:
            leave_sudo = self._document_check_access('hr.leave', leave_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        
        # if leave_sudo:
        #     # store the date as a string in the session to allow serialization
        #     now = fields.Date.today().isoformat()
        #     session_obj_date = request.session.get('view_leave_%s' % leave_sudo.id)
        #     if session_obj_date != now and request.env.user.share and access_token:
        #         request.session['view_leave_%s' % leave_sudo.id] = now
        #         body = _('Time Off viewed by customer %s', leave_sudo.employee_id.name)
        #         _message_post_helper(
        #             "hr.leave",
        #             leave_sudo.id,
        #             body,
        #             token=leave_sudo.access_token,
        #             message_type="notification",
        #             subtype_xmlid="mail.mt_note",
        #             partner_ids=leave_sudo.employee_id.sudo().user_id.ids,
        #         )
        #
        values = {
            'leave': leave_sudo,
            'token': access_token,
            'bootstrap_formatting': True,
            'report_type': 'html',
            'message': message,
            'partner_id': leave_sudo.employee_id.sudo().user_id.ids,
        }

        employee = leave_sudo.employee_id
        values.update({
            'holiday_types': self._prepare_portal_holiday_types(employee)
        })
        return request.render("pt_timeoff_portal.portal_my_leave", values)
    
    @http.route(['/my/leaves/summary'], type='http', auth="user", website=True)
    def leaves_summary(self):
        if not request.session.uid:
            return {'error': 'anonymous_user'}
        
        get_days_all_request = request.env['hr.leave.type'].with_user(request.session.uid).get_allocation_data_request()
        values = {
            'timeoffs': get_days_all_request,
            'page_name': 'leave_summary',
        }
        return request.render("pt_timeoff_portal.my_leaves_summary", values)
