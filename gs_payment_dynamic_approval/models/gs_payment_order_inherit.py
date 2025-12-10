from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class GSPaymentOrderInherit(models.Model):
    _inherit = 'gs.payment.order'

    approval_level_id = fields.Many2one(
        'gs.payment.approval.config', string="Approval Level", compute="compute_approval_level")

    level = fields.Integer(string="Next Approval Level", readonly=True)
    user_ids = fields.Many2many('res.users', string="Users", readonly=True)
    group_ids = fields.Many2many('res.groups', string="Groups", readonly=True)
    is_boolean = fields.Boolean(
        string="Boolean", compute="compute_is_boolean", search='_search_is_boolean')
    approval_info_line = fields.One2many(
        'gs.approval.info', 'payment_order_id', readonly=True)
    rejection_date = fields.Datetime(string="Reject Date", readonly=True)
    reject_by = fields.Many2one('res.users', string="Reject By", readonly=True)
    reject_reason = fields.Char(string="Reject Reason", readonly=True)

    def compute_is_boolean(self):
        if self.env.user.id in self.user_ids.ids or any(item in self.env.user.groups_id.ids for item in self.group_ids.ids):
            self.is_boolean = True
        else:
            self.is_boolean = False

    def _search_is_boolean(self, operator, value):
        results = []

        if value:
            payment_order_ids = self.env['gs.payment.order'].search([])
            if payment_order_ids:
                for payment_order_id in payment_order_ids:
                    if self.env.user.id in payment_order_id.user_ids.ids or any(item in self.env.user.groups_id.ids for item in payment_order_id.group_ids.ids):
                        results.append(payment_order_id.id)
        return [('id', 'in', results)]

    def action_submit(self):
        template_id = self.env.ref("gs_payment_dynamic_approval.email_template_for_approve_payment_order")

        self.approval_info_line = False
        self.level = False
        self.group_ids = False
        self.user_ids = False

        if self.approval_level_id.payment_approval_line:

            lines = self.approval_level_id.payment_approval_line

            for line in lines:
                dictt = []
                if line.approve_by == 'group':
                    dictt.append((0, 0, {
                        'level': line.level,
                        'user_ids': False,
                        'group_ids': [(6, 0, line.group_ids.ids)],
                    }))

                if line.approve_by == 'user':
                    dictt.append((0, 0, {
                        'level': line.level,
                        'user_ids': [(6, 0, line.user_ids.ids)],
                        'group_ids': False,
                    }))

                self.update({
                    'approval_info_line': dictt
                })

            if lines[0].approve_by == 'group':
                self.write({
                    'level': lines[0].level,
                    'group_ids': [(6, 0, lines[0].group_ids.ids)],
                    'user_ids': False
                })

                users = self.env['res.users'].search(
                    [('groups_id', 'in', lines[0].group_ids.ids)])

                if template_id and users:
                    for user in users:
                        template_id.sudo().send_mail(self.id, force_send=True, email_values={
                            'email_from': self.env.user.email, 'email_to': user.email})

                notifications = []
                if users:
                    for user in users:
                        notifications.append([
                            (user.partner_id.id, 'mail.message/notification_update'),
                            (self._cr.dbname, 'res.partner', user.partner_id.id),
                            {'type': 'user_connection', 'title': _(
                                'Notitification'), 'message': 'You have approval notification for Payment Order %s' % (self.name), 'sticky': True, 'warning': True}])
                    print("nnnn111", notifications)
                    self.env['bus.bus']._sendone(notifications)

            if lines[0].approve_by == 'user':
                self.write({
                    'level': lines[0].level,
                    'user_ids': [(6, 0, lines[0].user_ids.ids)],
                    'group_ids': False
                })

                if template_id and lines[0].user_ids:
                    for user in lines[0].user_ids:
                        template_id.sudo().send_mail(self.id, force_send=True, email_values={
                            'email_from': self.env.user.email, 'email_to': user.email})

                notifications = []
                if lines[0].user_ids:
                    for user in lines[0].user_ids:
                        notifications.append([
                            (user.partner_id.id, 'mail.message/notification_update'),
                            (self._cr.dbname, 'res.partner', user.partner_id.id),
                            {'type': 'user_connection', 'title': _('Notitification'), 'message': 'You have approval notification for Payment Order %s' % (self.name), 'sticky': True, 'warning': True}])
                    print("nnnn222", notifications)
                    self.env['bus.bus']._sendone(notifications)

            super(GSPaymentOrderInherit, self).action_submit()
        else:
            super(GSPaymentOrderInherit, self).action_submit()

    @api.depends('amount', 'payment_type_id')
    def compute_approval_level(self):

        if self.amount or self.payment_type_id:

            payment_approvals = self.env['gs.payment.approval.config'].search(
                [('min_amount', '<=', self.amount), ('company_ids.id', 'in', [self.env.company.id])])

            listt = []
            list2 = 0
            for payment_approval in payment_approvals:
                if self.payment_type_id in payment_approval.payment_type_ids:
                    listt.append(payment_approval.min_amount)
                    list2 = payment_approval.id

            if listt:
                self.approval_level_id = list2
            else:
                self.approval_level_id = False
        else:
            self.approval_level_id = False

    def action_approve(self):

        template_id = self.env.ref(
            "gs_payment_dynamic_approval.email_template_for_approve_payment_order")

        info = self.approval_info_line.filtered(
            lambda x: x.level == self.level)

        if info:
            info.status = True
            info.approval_date = datetime.now()
            info.approved_by = self.env.user

        line_id = self.env['gs.payment.approval.line'].search(
            [('payment_approval_config_id', '=', self.approval_level_id.id), ('level', '=', self.level)])

        next_line = self.env['gs.payment.approval.line'].search(
            [('payment_approval_config_id', '=', self.approval_level_id.id), ('id', '>', line_id.id)], limit=1)

        if next_line:
            if next_line.approve_by == 'group':
                self.write({
                    'level': next_line.level,
                    'group_ids': [(6, 0, next_line.group_ids.ids)],
                    'user_ids': False
                })
                users = self.env['res.users'].search(
                    [('groups_id', 'in', next_line.group_ids.ids)])

                if template_id and users and self.approval_level_id.is_boolean:
                    for user in users:
                        template_id.sudo().send_mail(self.id, force_send=True, email_values={
                            'email_from': self.env.user.email, 'email_to': user.email, 'email_cc': self.partner_id.email})

                if template_id and users and not self.approval_level_id.is_boolean:
                    for user in users:
                        template_id.sudo().send_mail(self.id, force_send=True, email_values={
                            'email_from': self.env.user.email, 'email_to': user.email})

                notifications = []
                if users:
                    for user in users:
                        notifications.append([
                            (user.partner_id.id, 'mail.message/notification_update'),
                            (self._cr.dbname, 'res.partner', user.partner_id.id),
                            {'type': 'user_connection', 'title': _(
                                'Notitification'), 'message': 'You have approval notification for Payment Order %s' % (self.name), 'sticky': True, 'warning': True}])
                    self.env['bus.bus']._sendone(notifications)

            if next_line.approve_by == 'user':
                self.write({
                    'level': next_line.level,
                    'user_ids': [(6, 0, next_line.user_ids.ids)],
                    'group_ids': False
                })

                if template_id and next_line.user_ids and self.approval_level_id.is_boolean:
                    for user in next_line.user_ids:
                        template_id.sudo().send_mail(self.id, force_send=True, email_values={
                            'email_from': self.env.user.email, 'email_to': user.email, 'email_cc': self.partner_id.email})

                if template_id and next_line.user_ids and not self.approval_level_id.is_boolean:
                    for user in next_line.user_ids:
                        template_id.sudo().send_mail(self.id, force_send=True, email_values={
                            'email_from': self.env.user.email, 'email_to': user.email})

                notifications = []
                if next_line.user_ids:
                    for user in next_line.user_ids:
                        notifications.append([
                            (user.partner_id.id, 'mail.message/notification_update'),
                            (self._cr.dbname, 'res.partner', user.partner_id.id),
                            {'type': 'user_connection', 'title': _(
                                'Notitification'), 'message': 'You have approval notification for Payment Order %s' % (self.name), 'sticky': True, 'warning': True}])
                    self.env['bus.bus']._sendone(notifications)

        else:
            template_id = self.env.ref(
                "gs_payment_dynamic_approval.email_template_for_confirm_payment_order")
            if template_id:
                template_id.sudo().send_mail(self.id, force_send=True, email_values={
                    'email_from': self.env.user.email, 'email_to': self.partner_id.email})

            notifications = []
            if self.partner_id:
                notifications.append([
                    (self.partner_id.id, 'mail.message/notification_update'),
                    (self._cr.dbname, 'res.partner', self.partner_id.id),
                    {'type': 'user_connection', 'title': _(
                        'Notitification'), 'message': 'Your Payment Order %s is approved' % (self.name), 'sticky': True, 'warning': True}])
                self.env['bus.bus']._sendmany(notifications)

            self.write({
                'level': False,
                'group_ids': False,
                'user_ids': False,
                'state': 'approve'
            })

            super(GSPaymentOrderInherit, self).action_approve()

    def action_approve_new(self):

        super(GSPaymentOrderInherit, self).action_approve()