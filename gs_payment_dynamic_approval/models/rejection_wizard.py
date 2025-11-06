from odoo import api, fields, tools, models, _
from datetime import datetime


class RejectionReasonWizard(models.TransientModel):
    _inherit = 'gs.payment.reason.wizard'

    # name = fields.Char(string="Reason", required=True)

    def action_reject_order(self):

        active_obj = self.env[self.env.context.get('active_model')].browse(
            self.env.context.get('active_id'))

        if self.env.context.get('active_model') == 'gs.payment.order':

            active_obj.write({
                'reject_reason': self.name,
                'reject_by': active_obj.env.user,
                'rejection_date': datetime.now(),
                'state': 'refused',
            })

            template_id = active_obj.env.ref(
                "gs_payment_dynamic_approval.email_template_for_reject_payment_order")

            if template_id:
                template_id.sudo().send_mail(active_obj.id, force_send=True, email_values={
                    'email_from': active_obj.env.user.email, 'email_to': active_obj.partner_id.email})

            notifications = []
            if active_obj.partner_id:
                notifications.append([
                    (active_obj._cr.dbname, 'res.partner',
                    active_obj.partner_id.id),
                    {'type': 'user_connection', 'title': _(
                        'Notitification'), 'message': 'Your Payment Order %s is rejected' % (active_obj.description), 'sticky': True, 'warning': True}])
                active_obj.env['bus.bus'].sendmany(notifications)

        return super(RejectionReasonWizard,self).action_reject_order()