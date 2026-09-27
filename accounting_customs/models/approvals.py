from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from markupsafe import Markup

SAUDI_BANKS = {
    "05": {
        "name": "Alinma Bank",
        "swift": "INMASARI",
    },
    "10": {
        "name": "Saudi National Bank",
        "swift": "NCBKSAJE",
    },
    "15": {
        "name": "Bank Albilad",
        "swift": "ALBISARI",
    },
    "20": {
        "name": "Riyad Bank",
        "swift": "RIBLSARI",
    },
    "30": {
        "name": "Arab National Bank",
        "swift": "ARNBSARI",
    },
    "40": {
        "name": "Saudi Awwal Bank",
        "swift": "SABBSARI",
    },
    "45": {
        "name": "Saudi Awwal Bank",
        "swift": "SABBSARI",
    },
    "50": {
        "name": "Banque Saudi Fransi",
        "swift": "BSFRSARI",
    },
    "55": {
        "name": "Banque Saudi Fransi",
        "swift": "BSFRSARI",
    },
    "60": {
        "name": "Bank AlJazira",
        "swift": "BJAZSAJE",
    },
    "65": {
        "name": "Saudi Awwal Bank",
        "swift": "SABBSARI",
    },
    "80": {
        "name": "Al Rajhi Bank",
        "swift": "RJHISARI",
    },
    "36": {
        "name": "D360 Bank",
        "swift": "DBAKSARI",
    },
    "78": {
        "name": "STC Bank",
        "swift": "STCJSARI",
    },
}

class ApprovalRequestInherit(models.Model):
    _inherit = 'approval.request'

    name = fields.Char( string="Approval ID",)
    has_purchase_order = fields.Boolean(related="category_id.has_purchase_order")
    has_sale_order = fields.Boolean(related="category_id.has_sale_order")
    has_paid = fields.Boolean(related="category_id.has_paid")
    purchase_order_id = fields.Many2one("purchase.order", tracking=True,)
    sale_order_id = fields.Many2one("sale.order", tracking=True,)
    currency_id = fields.Many2one("res.currency", tracking=True, default=lambda self: self.env.company.currency_id,)
    payment_method = fields.Selection([('transfer', 'Transfer'), ('cash', 'Cash'), ('sadad', 'Sadad')], tracking=True)
    beneficiary_account_name = fields.Char(tracking=True)
    beneficiary_iban = fields.Char("Beneficiary IBAN", tracking=True)
    beneficiary_bank = fields.Char(tracking=True)
    swiftcode = fields.Char("SWIFT Code", tracking=True)
    sadad_ref = fields.Char("SADAD Ref", tracking=True)
    sadad_account = fields.Char("SADAD Account", tracking=True)
    can_mark_ready_to_transfer = fields.Boolean( compute="_compute_can_mark_ready_to_transfer", )
    can_mark_paid = fields.Boolean( compute="_compute_can_mark_paid",)
    can_cancel_ready = fields.Boolean(compute="_compute_can_cancel_ready")

    is_ready_to_transfer = fields.Boolean( string="Ready for Transfer", copy=False, )

    is_paid = fields.Boolean(string="Paid", copy=False,)

    payment_attachment_ids = fields.Many2many(
            comodel_name="ir.attachment",
            relation="approval_request_payment_attachment_rel",
            column1="approval_request_id",
            column2="attachment_id",
            string="Payment Attachments",
            copy=False,
        )

    payment_attachment_filename = fields.Char( copy=False,)
    payment_date = fields.Date(tracking=True, copy=False,)

    request_status = fields.Selection(
        selection_add=[
            ("new", "Draft"),
            ("ready_to_transfer", "Ready for Transfer"),
            ("paid", "Paid"),
            ("refused",),
        ],
        ondelete={
            "ready_to_transfer": "set default",
            "paid": "set default",
        },
    )

    approval_waiting_display = fields.Char(
    string="Current Approval Stage",
        compute="_compute_approval_waiting_display",
    )


    payment_count = fields.Integer(
        string="Payments",
        compute="_compute_payment_count",
    )

    @api.model_create_multi
    def create(self, vals_list):
        requests = super().create(vals_list)

        for request in requests:
            sequence_number = self.env["ir.sequence"].next_by_code("approval.request") or "0000001"
            category_code = (request.category_id.sequence_code or "").strip().upper()
            request.name = f"{category_code}{sequence_number}" if category_code else sequence_number

            follower_partners = request.category_id.allowed_for_all_approvals.mapped("partner_id")
            if follower_partners:
                request.message_subscribe(partner_ids=follower_partners.ids)

        return requests

    def _compute_payment_count(self):
        for request in self:
            request.payment_count = self.env['account.payment'].search_count([("approval_id", "=", request.id),])

    @api.depends(
        "request_status",
        "approver_ids.status",
        "approver_ids.user_id",
        "category_id.approver_ids.user_id",
        "category_id.approver_ids.stage",
    )
    def _compute_approval_waiting_display(self):
        for request in self:
            request.approval_waiting_display = False

            if request.request_status != "pending":
                continue

            pending_approver = request.approver_ids.filtered(
                lambda approver: (
                    approver.status == "pending"
                    and approver.user_id
                )
            )[:1]

            if not pending_approver:
                pending_approver = request.approver_ids.filtered(
                    lambda approver: (
                        approver.status == "waiting"
                        and approver.user_id
                    )
                )[:1]

            if not pending_approver:
                continue

            user_name = pending_approver.user_id.display_name

            category_approver = request.category_id.approver_ids.filtered(
                lambda approver: (
                    approver.user_id == pending_approver.user_id
                )
            )[:1]

            if category_approver.stage:
                request.approval_waiting_display = _(
                    "%s: %s"
                ) % (
                    category_approver.stage,
                    user_name,
                )
            else:
                request.approval_waiting_display = _(
                    "Waiting for: %s"
                ) % user_name

    def unlink(self):
        for request in self:
            if request.request_status != "new":
                raise ValidationError(
                    _(
                        "You cannot delete an approval request "
                        "after it has been submitted."
                    )
                )

            if request.create_uid != self.env.user:
                raise ValidationError(
                    _("Only the request creator can delete this approval request.")
                )

        return super().unlink()

    def action_confirm(self):
        for request in self:
            if (
                request.category_id.has_amount == "required"
                and request.amount <= 0
            ):
                raise ValidationError(
                    _(
                        "You can't submit a request with a zero amount."
                    )
                )

        return super().action_confirm()

    @api.depends("approver_ids.status", "is_ready_to_transfer", "is_paid",)
    def _compute_request_status(self):
        super()._compute_request_status()

        for request in self:
            if request.is_paid:
                request.request_status = "paid"
            elif request.is_ready_to_transfer:
                request.request_status = "ready_to_transfer"

    @api.onchange("beneficiary_iban")
    def _onchange_beneficiary_iban(self):
        for record in self:
            record.beneficiary_bank = False
            record.swiftcode = False

            if not record.beneficiary_iban:
                continue

            iban = "".join(
                character
                for character in record.beneficiary_iban.upper()
                if character.isalnum()
            )

            record.beneficiary_iban = iban

            if not iban.startswith("SA") or len(iban) < 6:
                continue

            bank_code = iban[4:6]
            bank_data = SAUDI_BANKS.get(bank_code)

            if bank_data:
                record.beneficiary_bank = bank_data["name"]
                record.swiftcode = bank_data["swift"]

    @api.constrains("category_id")
    def _check_category_allowed_user(self):
        for request in self:
            category = request.category_id

            if (
                category.allowed_users_ids
                and self.env.user not in category.allowed_users_ids
            ):
                raise ValidationError(
                    _(
                        "You are not allowed to create an approval request "
                        "using the category '%s'."
                    )
                    % category.display_name
                )

    def action_approve(self, approver=None):
        result = super().action_approve(approver=approver)

        for request in self:
            if (
                request.request_status == "approved"
                and request.category_id.has_ready_to_transfer
            ):
                request._create_ready_to_transfer_activities()

        return result

    def _create_ready_to_transfer_activities(self):
        activity_type = self.env.ref(
            "mail.mail_activity_data_todo",
            raise_if_not_found=False,
        )

        if not activity_type:
            return

        model_id = self.env["ir.model"]._get_id(self._name)

        for request in self:
            responsible_users = (
                request.category_id.resposibles_for_transfer
            )

            for user in responsible_users:
                existing_activity = self.env["mail.activity"].search(
                    [
                        ("res_model_id", "=", model_id),
                        ("res_id", "=", request.id),
                        ("activity_type_id", "=", activity_type.id),
                        ("user_id", "=", user.id),
                        ("summary", "=", "Approved Request"),
                    ],
                    limit=1,
                )

                if existing_activity:
                    continue

                request.activity_schedule(
                    act_type_xmlid="mail.mail_activity_data_todo",
                    user_id=user.id,
                    date_deadline=fields.Date.context_today(request),
                    summary=_("Approved Request"),
                    note=_(
                        "The approval request has been approved "
                        "and is waiting for your action."
                    ),
                )

    def _remove_ready_to_transfer_activities(self):
        model_id = self.env["ir.model"]._get_id(self._name)

        activities = self.env["mail.activity"].search(
            [
                ("res_model_id", "=", model_id),
                ("res_id", "in", self.ids),
                ("summary", "=", "Approved Request"),
            ]
        )

        activities.unlink()

    def action_withdraw(self):
        result = super().action_withdraw()
        self._remove_ready_to_transfer_activities()
        return result

    def action_cancel(self):
        result = super().action_cancel()
        self._remove_ready_to_transfer_activities()
        return result

    @api.depends_context("uid")
    def _compute_can_mark_ready_to_transfer(self):
        current_user = self.env.user

        for request in self:
            request.can_mark_ready_to_transfer = bool(
                request.request_status == "approved"
                and request.category_id.has_ready_to_transfer
                and current_user
                in request.category_id.resposibles_for_transfer
                and not request.is_ready_to_transfer
            )

    def action_ready_to_transfer(self):
        for request in self:
            if request.request_status != "approved":
                raise ValidationError(
                    _("Only an approved request can be marked as ready for transfer.")
                )

            if not request.category_id.has_ready_to_transfer:
                raise ValidationError(
                    _("Ready for Transfer is not enabled for this category.")
                )

            if (
                self.env.user
                not in request.category_id.resposibles_for_transfer
            ):
                raise ValidationError(
                    _("You are not responsible for transferring this request.")
                )

            request.write({
                "is_ready_to_transfer": True,
            })

            request._remove_ready_to_transfer_activities()

        return True

    @api.depends(
        "request_status",
        "category_id.has_paid",
        "category_id.resposibles_for_payment",
        "is_paid",
    )
    @api.depends_context("uid")
    def _compute_can_mark_paid(self):
        current_user = self.env.user

        for request in self:
            request.can_mark_paid = bool(
                request.request_status == "ready_to_transfer"
                and request.category_id.has_paid
                and current_user in request.category_id.resposibles_for_payment
                and not request.is_paid
            )

    def action_set_paid(self):
        for request in self:
            if request.request_status != "ready_to_transfer":
                raise ValidationError(
                    _(
                        "Only a request that is Ready for Transfer "
                        "can be marked as Paid."
                    )
                )

            if not request.category_id.has_paid:
                raise ValidationError(
                    _("Paid status is not enabled for this category.")
                )

            if (
                self.env.user
                not in request.category_id.resposibles_for_payment
            ):
                raise ValidationError(
                    _(
                        "You are not responsible for marking "
                        "this request as paid."
                    )
                )

            if not request.payment_date:
                raise ValidationError(
                    _(
                        "Please set the payment date before "
                        "marking the request as paid."
                    )
                )

            if not request.payment_attachment_ids and request.payment_method != 'sadad':
                raise ValidationError(
                    _(
                        "Please attach the payment document before "
                        "marking the request as paid."
                    )
                )

            request.write({
                "is_paid": True,
                "is_ready_to_transfer": True,
            })

            request._remove_payment_activities()

            requester_partner = request.request_owner_id.partner_id

            if requester_partner:
                request.message_post(
                    body=Markup(
                        '<a href="#" '
                        'data-oe-model="res.partner" '
                        'data-oe-id="%s">'
                        '@%s'
                        '</a> '
                        'Your approval request has been paid.'
                    ) % (
                        requester_partner.id,
                        requester_partner.display_name,
                    ),
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                    partner_ids=requester_partner.ids,
                )
            else:
                request.message_post(
                    body=_("The approval request has been paid."),
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                )

        return True

    def _remove_payment_activities(self):
        if not self:
            return

        model_id = self.env["ir.model"]._get_id(self._name)

        activities = self.env["mail.activity"].search([
            ("res_model_id", "=", model_id),
            ("res_id", "in", self.ids),
            ("summary", "=", "Ready for Payment"),
        ])

        activities.unlink()

    def action_account_payment(self):
        return {
            'name': _('Payments'),
            'domain': [('approval_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'account.payment',
            'view_id': False,
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
            'context': {'default_approval_id': self.id, 
                'default_partner_id': self.partner_id.id, 
                'default_payment_type': 'outbound',
                'default_amount': self.amount,
                'default_currency_id': self.currency_id.id,
                'default_memo': self.reference,
                }
        }

    @api.onchange("partner_id", "payment_method")
    def _onchange_partner_bank_details(self):
        for request in self:
            request.beneficiary_account_name = False
            request.beneficiary_iban = False
            request.beneficiary_bank = False
            request.swiftcode = False

            if not request.partner_id or request.payment_method != "transfer":
                continue

            bank_account = request.partner_id.bank_ids[:1]

            if not bank_account:
                continue

            request.beneficiary_account_name = (
                bank_account.acc_holder_name
                or request.partner_id.display_name
            )
            request.beneficiary_iban = bank_account.acc_number

    @api.depends("request_status", "category_id.allowed_cancel_ready")
    @api.depends_context("uid")
    def _compute_can_cancel_ready(self):
        for request in self:
            request.can_cancel_ready = bool(
                request.request_status == "ready_to_transfer"
                and self.env.user in request.category_id.allowed_cancel_ready
            )

    def action_cancel_ready(self):
        self.write({
            "is_ready_to_transfer": False,
            "is_paid": False,
        })
        result = super().action_cancel()
        self._remove_ready_to_transfer_activities()
        self._remove_payment_activities()
        return result

    waiting_for_my_approval = fields.Boolean(compute="_compute_waiting_for_my_approval", search="_search_waiting_for_my_approval",)

    @api.depends("approver_ids.user_id", "approver_ids.status",)
    def _compute_waiting_for_my_approval(self):
        current_user = self.env.user

        for request in self:
            request.waiting_for_my_approval = any(
                approver.user_id == current_user and approver.status == "pending"
                for approver in request.approver_ids
            )

    def _search_waiting_for_my_approval(self, operator, value):
        approver_domain = [
            ("user_id", "=", self.env.user.id),
            ("status", "=", "pending"),
        ]

        approver_request_ids = self.env["approval.approver"].search(approver_domain).mapped("request_id").ids

        if (operator == "=" and value) or (operator == "!=" and not value):
            return [("id", "in", approver_request_ids)]

        return [("id", "not in", approver_request_ids)]

class ApprovalCategoryInherit(models.Model):
    _inherit = 'approval.category'

    has_purchase_order = fields.Boolean()
    has_sale_order = fields.Boolean()

    has_ready_to_transfer = fields.Boolean()
    resposibles_for_transfer = fields.Many2many("res.users",relation="approval_category_transfer_user_rel", column1="category_id", column2="user_id",)
    allowed_cancel_ready = fields.Many2many("res.users",relation="approval_category_allowed_cancel_ready_rel", column1="category_id", column2="user_id",)
    has_paid = fields.Boolean()
    resposibles_for_payment = fields.Many2many("res.users", relation="approval_category_payment_user_rel", column1="category_id", column2="user_id",)

    allowed_users_ids = fields.Many2many("res.users", string="Allowed For Creation", relation="approval_category_allowed_user_rel", column1="category_id", column2="user_id", help="Users allowed to create requests using this category. "
            "If empty, the category is available to all users.",)
    allowed_for_all_approvals = fields.Many2many("res.users", string="Allowed To See All Approvals",relation="approval_category_allowed_for_all_approvals_rel", column1="category_id", column2="user_id",)

class ApprovalCategoryApproverInherit(models.Model):
    _inherit = 'approval.category.approver'

    stage = fields.Char()

class IrAttachmentInherit(models.Model):
    _inherit = "ir.attachment"

    def unlink(self):
        approval_attachments = self.filtered(lambda attachment: attachment.res_model == "approval.request" and attachment.res_id)

        if approval_attachments:
            requests = self.env["approval.request"].sudo().search([
                ("id", "in", approval_attachments.mapped("res_id")),
                ("request_status", "!=", "new"),
            ])

            if requests:
                raise ValidationError(
                    _("Attachments can only be deleted while the approval request is in Draft status.")
                )

        payment_requests = self.env["approval.request"].sudo().search([
            ("payment_attachment_ids", "in", self.ids),
            ("request_status", "!=", "new"),
        ])

        if payment_requests:
            raise ValidationError(
                _("Attachments can only be deleted while the approval request is in Draft status.")
            )

        return super().unlink()