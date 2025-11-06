# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import datetime
from datetime import datetime, date, timedelta


class CreatePaymentWizard(models.TransientModel):
    _name = 'gs.return.wizard'

    state = fields.Selection(string='State', selection=[
                                                    ('draft', 'Draft'),
                                                    ('submit', 'Submitted'),
                                                    ('checked', 'Checked'),
                                                    ('approve', 'Approved'),
                                                    ('special_approval', 'Special Approval'),
                                                    ('special_approved', 'Special Approved'),
                                                    ('issue_payment', 'Issue Payment'),
                                                    ('finalize_payment', 'Finalize Payment'),
                                                    ('final_check', 'Final Check'),
                                                    ('close', 'Closed'),
                                                    ])

    return_comment = fields.Text(string="Return Comment")

    def return_wizard(self):
        active_id = self.env.context.get('active_id')
        request_object = self.env['gs.payment.order'].search([('id', '=', active_id)])
        if request_object.state == 'submit':
            if not self.state == 'draft':
                raise ValidationError(_("can't set this state you should set state before this state ( Submitted )"))
        elif request_object.state == 'checked':
            if not self.state in ['draft', 'submit']:
                raise ValidationError(_("can't set this state you should set state before this state ( Checked )"))
        elif request_object.state == 'approve':
            if not self.state in ['draft', 'submit', 'checked']:
                raise ValidationError(_("can't set this state you should set state before this state ( Approved )"))

        elif request_object.state == 'special_approval':
            if not self.state in ['draft', 'submit', 'checked', 'approve']:
                raise ValidationError(_("can't set this state you should set state before this state ( Special Approval )"))

        elif request_object.state == 'special_approved':
            if not self.state in ['draft', 'submit', 'checked', 'approve', 'special_approval']:
                raise ValidationError(_("can't set this state you should set state before this state ( Special Approved )"))

        elif request_object.state == 'issue_payment':
            if not self.state in ['draft', 'submit', 'checked', 'approve', 'special_approval', 'special_approved']:
                raise ValidationError(_("can't set this state you should set state before this state ( Issue Payment )"))

        elif request_object.state == 'finalize_payment':
            if not self.state in ['draft', 'submit', 'checked', 'approve', 'special_approval', 'special_approved', 'issue_payment']:
                raise ValidationError(_("can't set this state you should set state before this state ( Finalize Payment )"))

        elif request_object.state == 'finalize_payment':
            if not self.state in ['draft', 'submit', 'checked', 'approve', 'special_approval', 'special_approved', 'issue_payment']:
                raise ValidationError(_("can't set this state you should set state before this state ( Finalize Payment )"))

        elif request_object.state == 'final_check':
            if not self.state in ['draft', 'submit', 'checked', 'approve', 'special_approval', 'special_approved', 'issue_payment', 'finalize_payment']:
                raise ValidationError(_("can't set this state you should set state before this state ( Final Check )"))

        elif request_object.state == 'close':
            if not self.state in ['draft', 'submit', 'checked', 'approve', 'special_approval', 'special_approved', 'issue_payment', 'finalize_payment', 'final_check']:
                raise ValidationError(_("can't set this state you should set state before this state ( Closed )"))

        request_object.state = self.state
        note = ' '
        if self.return_comment:
            note = ' ( ' + str(self.return_comment) + ' )'
        request_object.payment_order_history_ids.create(
            {
                "payment_order_id": request_object.id,
                "date": datetime.now(),
                "note": note,
                "user_id": self.env.user.id
            }
        )