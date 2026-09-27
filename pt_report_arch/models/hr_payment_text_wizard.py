from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
from datetime import datetime,date
import calendar


class HrPaymentTextWizard(models.TransientModel):
    _name = "hr.payment.text.wizard"
    _description = "HR Payment Text File Wizard"

    payment_company_id = fields.Many2one(
        "payment.company",
        string="Company ID",
        required=True,
    )

    payment_scope = fields.Selection(
        [
            ("company", "Company"),
            ("employee", "Employee"),
            ("enroll_employee", "Enroll Employee"),
        ],
        string="Print For",
        required=True,
        default="company",
    )
    enroll_employee_id = fields.Many2one(
        "enrol.employee",
        string="Enroll Employee",
    )

    payment_date = fields.Date(
        string="Payment Date",
        required=True,
        default=fields.Date.context_today,
    )
    period_from = fields.Date(
        string="Period From",
        required=True,
        default=fields.Date.context_today,
    )

    period_to = fields.Date(
        string="Period To",
        required=True,
    )

    period_display = fields.Char(
        string="Period",
        compute="_compute_period_display",
    )

    available_employee_ids = fields.Many2many(
        "hr.employee",
        string="Available Employees",
        compute="_compute_available_employee_ids",
    )

    employee_ids = fields.Many2many(
        "hr.employee",
        string="Employees",
        domain="[('id', 'in', available_employee_ids)]",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.ref("base.SAR", raise_if_not_found=False),
    )

    payment_method = fields.Selection(
        [
            ("ach_payments", "ACH payments"),
            ("pp_vendor_payment", "PP (vendor payment)"),
            ("saudi_ach_credits", "Saudi ACH credits"),
        ],
        string="Payment Method",
        required=True,
        default="saudi_ach_credits",
    )

    file_data = fields.Binary(string="Text File", readonly=True)
    file_name = fields.Char(string="File Name", readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        period_from = res.get("period_from") or fields.Date.context_today(self)
        from_date = fields.Date.to_date(period_from)

        last_day_number = calendar.monthrange(from_date.year, from_date.month)[1]

        res["period_from"] = from_date
        res["period_to"] = date(from_date.year, from_date.month, last_day_number)

        return res

    def _format_amount(self, amount):
        amount = amount or 0
        amount = round(amount, 2)

        if amount == int(amount):
            return str(int(amount))

        return str(amount)

    def _get_company_payment_id(self):
        self.ensure_one()

        company_payment_id = self.payment_company_id.company_id_number

        if not company_payment_id:
            raise UserError("Please set Company ID Number on the selected company.")

        return company_payment_id

    @api.depends("period_from", "period_to", "payment_scope", "enroll_employee_id")
    def _compute_available_employee_ids(self):
        for wizard in self:
            if not wizard.period_from or not wizard.period_to:
                wizard.available_employee_ids = False
                continue

            payslips = self.env["hr.payslip"].search([
                ("date_from", ">=", wizard.period_from),
                ("date_to", "<=", wizard.period_to),
                ("state", "in", ["done", "paid"]),
            ])

            employees = payslips.mapped("employee_id")

            if wizard.payment_scope == "enroll_employee":
                if wizard.enroll_employee_id:
                    employees = employees.filtered(
                        lambda emp: emp.enrol_employee_id.id == wizard.enroll_employee_id.id
                    )
                else:
                    employees = employees.filtered(
                        lambda emp: not emp.enrol_employee_id
                    )

            wizard.available_employee_ids = employees

    @api.depends("period_from", "period_to")
    def _compute_period_display(self):
        for wizard in self:
            if wizard.period_from and wizard.period_to:
                period_from = fields.Date.to_date(wizard.period_from).strftime("%m/%d/%Y")
                period_to = fields.Date.to_date(wizard.period_to).strftime("%m/%d/%Y")
                wizard.period_display = f"{period_from} - {period_to}"
            else:
                wizard.period_display = ""

    @api.onchange("payment_scope", "period_from", "period_to", "enroll_employee_id")
    def _onchange_payment_scope_or_period(self):
        self.employee_ids = False

        if self.payment_scope != "enroll_employee":
            self.enroll_employee_id = False

    @api.onchange("period_from")
    def _onchange_period_from(self):
        for wizard in self:
            if not wizard.period_from:
                wizard.period_to = False
                continue

            from_date = fields.Date.to_date(wizard.period_from)

            last_day_number = calendar.monthrange(from_date.year, from_date.month)[1]
            wizard.period_to = date(from_date.year, from_date.month, last_day_number)

    def _get_payment_code(self):
        self.ensure_one()
        if self.payment_method == "ach_payments":
            return "ACH"
        if self.payment_method == "pp_vendor_payment":
            return "PP"
        return "ACH-CR"

    def _get_payslips_by_period(self):
        self.ensure_one()

        if self.period_from > self.period_to:
            raise UserError("Period From cannot be after Period To.")

        domain = [
            ("date_from", ">=", self.period_from),
            ("date_to", "<=", self.period_to),
            ("state", "in", ["done", "paid"]),
        ]

        if self.payment_scope == "employee":
            if not self.employee_ids:
                raise UserError("Please select at least one employee.")

            domain.append(("employee_id", "in", self.employee_ids.ids))

        elif self.payment_scope == "enroll_employee":
            if self.enroll_employee_id:
                domain.append(("employee_id.enrol_employee_id", "=", self.enroll_employee_id.id))
            else:
                domain.append(("employee_id.enrol_employee_id", "=", False))

        return self.env["hr.payslip"].search(domain)

    def _get_payslip_rule_amount(self, payslip, code):
        line = payslip.line_ids.filtered(lambda l: l.code == code)[:1]
        return line.total if line else 0

    def _get_bathdr_company_data(self):
        self.ensure_one()

        if self.payment_scope == "enroll_employee" and self.enroll_employee_id:
            enrol = self.enroll_employee_id

            return {
                "name": enrol.name or "",
                "cr": enrol.cr or "",
                "wol": enrol.wol or "",
            }

        return {
            "name": "",
            "cr": "",
            "wol": "",
        }

    def _get_non_zero_payslip_amounts(self, payslip):
        amounts = []

        for line in payslip.line_ids:
            if line.total:
                amounts.append(self._format_amount(line.total))

        return amounts

    def _prepare_secpty_line(self, payslip):
        employee = payslip.employee_id

        bank_account = employee.bank_account_id or employee.bank_account_id2

        iban = bank_account.acc_number if bank_account else ""
        employee_name = employee.name or ""
        employee_code = employee.registration_number2 or ""
        employee_id_number = employee.identification_id or ""

        total_amount = payslip.net_wage or 0

        basic_amount = self._get_payslip_rule_amount(payslip, "BASIC")
        housing_amount = self._get_payslip_rule_amount(payslip, "HOUALLOW")
        transportation_amount = self._get_payslip_rule_amount(payslip, "TRAALLOW")
        food_amount = self._get_payslip_rule_amount(payslip, "FA")
        other_allowance_amount = self._get_payslip_rule_amount(payslip, "OTALLOW")

        loan_amount = self._get_payslip_rule_amount(payslip, "loan")
        # absence_amount = self._get_payslip_rule_amount(payslip, "ABS")
        # eos_amount = self._get_payslip_rule_amount(payslip, "EOS")
        # paid_time_off_amount = self._get_payslip_rule_amount(payslip, "PAID86")
        paid_time_off_ded_amount = self._get_payslip_rule_amount(payslip, "PAID87")

        return (
            f"SECPTY,"
            f"{iban},"
            f"{employee_name},"
            f"{employee_code},"
            f"NCLBSAJD,"
            f",,,{self._format_amount(total_amount)},"
            f",,,,,,,N,N,"
            f",,,,,,@SACH@,"
            f"{employee_id_number},"
            f"{self._format_amount(basic_amount)},"
            f"{self._format_amount(housing_amount)},"
            f"{self._format_amount(transportation_amount)},"
            f"{self._format_amount(food_amount)},"
            f"{self._format_amount(other_allowance_amount)},"
            f"{self._format_amount(loan_amount)},"
            # f"{self._format_amount(absence_amount)},"
            # f"{self._format_amount(eos_amount)},"
            # f"{self._format_amount(paid_time_off_amount)},"
            f"{self._format_amount(paid_time_off_ded_amount)}"
        )

    def action_generate_text_file(self):
        self.ensure_one()

        now = datetime.now()

        date_slash = now.strftime("%Y/%m/%d")
        time_colon = now.strftime("%H:%M:%S")
        generate_date_plain = now.strftime("%Y%m%d")
        payment_date_plain = self.payment_date.strftime("%Y%m%d")
        payment_month_number = self.payment_date.month
        company_payment_id = self._get_company_payment_id()
        batch_ref = now.strftime("V217%y%m%d%H%M%S")
        conv_ref = now.strftime("CONV217%Y%m%d%H%M%S")

        payment_code = self._get_payment_code()

        payslips = self._get_payslips_by_period()

        if not payslips:
            raise UserError(
                "No confirmed/paid payslips found for the selected period: %s - %s."
                % (
                    self.period_from.strftime("%m/%d/%Y"),
                    self.period_to.strftime("%m/%d/%Y"),
                )
            )
        bathdr_company_data = self._get_bathdr_company_data()

        secpty_lines = []
        for payslip in payslips:
            secpty_lines.append(self._prepare_secpty_line(payslip))

        lines = [
            f"IFH,IFILE,CSV,,{company_payment_id},{conv_ref},{date_slash},{time_colon},P,1,{payment_month_number}",
            f"BATHDR,{payment_code},2,,,,S,WPSSalary1010433185,,@1ST@,{payment_date_plain},259141414001,{self.currency_id.name},,,,,,,,,{bathdr_company_data['name']},{bathdr_company_data['cr']},{bathdr_company_data['wol']},,,,{batch_ref}",
        ]

        lines += secpty_lines

        content = "\r\n".join(lines)

        filename = f"payment_file_{generate_date_plain}_{now.strftime('%H%M%S')}.txt"

        self.write({
            "file_data": base64.b64encode(content.encode("utf-8")),
            "file_name": filename,
        })

        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.payment.text.wizard",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }