from collections import defaultdict
from datetime import datetime
from itertools import zip_longest

from odoo import _, fields, models


class PurchaseExcelReport(models.AbstractModel):
    _name = "report.inventory_customs.purchase_excel_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Purchase Excel Report"

    def _get_selection_label(self, record, field_name):
        field = record._fields.get(field_name)

        if not field:
            return ""

        value = record[field_name]

        if value in (False, None):
            return ""

        if not field.selection:
            return str(value)

        selection = field._description_selection(record.env)

        return dict(selection).get(value, str(value))

    def _get_secondary_quantity(self, record):
        if "sh_sec_qty" not in record._fields:
            return False

        value = record["sh_sec_qty"]

        if value is False or value is None:
            return False

        if isinstance(value, (int, float)):
            return value

        return False

    def _get_secondary_uom(self, record):
        if "sh_sec_uom" not in record._fields:
            return ""

        secondary_uom = record["sh_sec_uom"]

        if not secondary_uom:
            return ""

        if hasattr(secondary_uom, "display_name"):
            return secondary_uom.display_name or ""

        return str(secondary_uom)

    def _get_purchase_line_uom(self, purchase_line):
        if (
            "product_uom" in purchase_line._fields
            and purchase_line.product_uom
        ):
            return purchase_line.product_uom.display_name or ""

        if (
            "product_uom_id" in purchase_line._fields
            and purchase_line.product_uom_id
        ):
            return purchase_line.product_uom_id.display_name or ""

        return ""

    def _get_invoice_line_uom(self, invoice_line):
        if (
            "product_uom_id" in invoice_line._fields
            and invoice_line.product_uom_id
        ):
            return invoice_line.product_uom_id.display_name or ""

        if (
            "product_uom" in invoice_line._fields
            and invoice_line.product_uom
        ):
            return invoice_line.product_uom.display_name or ""

        return ""

    def _get_move_received_quantity(self, move):
        if "quantity" in move._fields:
            return move.quantity or 0.0

        if "quantity_done" in move._fields:
            return move.quantity_done or 0.0

        return 0.0

    def _get_purchase_branch(self, purchase_order):
        if "branch_id" in purchase_order._fields:
            return purchase_order.branch_id

        return False

    def _get_purchase_confirmation_date(self, purchase_order):
        if "date_approve" in purchase_order._fields:
            return purchase_order.date_approve

        return False

    def _get_product_type(self, purchase_line):
        product = purchase_line.product_id

        if not product:
            return ""

        if "detailed_type" in product._fields:
            return self._get_selection_label(
                product,
                "detailed_type",
            )

        if "type" in product._fields:
            return self._get_selection_label(
                product,
                "type",
            )

        return ""

    def _get_purchase_total_company_currency(self, purchase_order):
        company_currency = purchase_order.company_id.currency_id
        purchase_currency = purchase_order.currency_id

        if purchase_currency == company_currency:
            return abs(purchase_order.amount_total or 0.0)

        conversion_date = (
            purchase_order.date_order.date()
            if purchase_order.date_order
            else fields.Date.context_today(self)
        )

        converted_amount = purchase_currency._convert(
            purchase_order.amount_total,
            company_currency,
            purchase_order.company_id,
            conversion_date,
        )

        return abs(converted_amount)

    def _get_purchase_receipt_status(self, purchase_order):
        pickings = purchase_order.picking_ids.filtered(
            lambda picking: (
                picking.picking_type_id.code == "incoming"
                and picking.state != "cancel"
            )
        )

        if not pickings:
            return _("Nothing Received")

        done_pickings = pickings.filtered(
            lambda picking: picking.state == "done"
        )

        if done_pickings and len(done_pickings) == len(pickings):
            return _("Fully Received")

        if done_pickings:
            return _("Partially Received")

        if pickings.filtered(
            lambda picking: picking.state == "assigned"
        ):
            return _("Ready")

        return _("Waiting")

    def _get_qualifying_move_domain(self, data):
        domain = [
            ("state", "=", "done"),
            ("picking_id", "!=", False),
            ("picking_id.state", "=", "done"),
            (
                "picking_id.picking_type_id.code",
                "=",
                "incoming",
            ),
            (
                "picking_id.date_done",
                ">=",
                data["date_from"],
            ),
            (
                "picking_id.date_done",
                "<=",
                data["date_to"],
            ),
            ("purchase_line_id", "!=", False),
            ("company_id", "in", data["company_ids"]),
        ]

        if "origin_returned_move_id" in self.env["stock.move"]._fields:
            domain.append(
                ("origin_returned_move_id", "=", False)
            )

        if (
            data.get("branch_ids")
            and "branch_id" in self.env["purchase.order"]._fields
        ):
            domain.append(
                (
                    "purchase_line_id.order_id.branch_id",
                    "in",
                    data["branch_ids"],
                )
            )

        if data.get("partner_ids"):
            domain.append(
                (
                    "purchase_line_id.order_id.partner_id",
                    "in",
                    data["partner_ids"],
                )
            )

        if data.get("purchase_order_ids"):
            domain.append(
                (
                    "purchase_line_id.order_id",
                    "in",
                    data["purchase_order_ids"],
                )
            )

        return domain

    def _get_invoice_lines_by_purchase_line(
        self,
        purchase_lines,
        include_cancelled_bills=False,
    ):
        result = defaultdict(
            lambda: self.env["account.move.line"]
        )

        if not purchase_lines:
            return result

        linked_domain = [
            (
                "purchase_line_id",
                "in",
                purchase_lines.ids,
            ),
            (
                "move_id.move_type",
                "in",
                ("in_invoice", "in_refund"),
            ),
            ("display_type", "=", "product"),
        ]

        if not include_cancelled_bills:
            linked_domain.append(
                ("move_id.state", "!=", "cancel")
            )

        linked_invoice_lines = self.env[
            "account.move.line"
        ].search(
            linked_domain,
            order="move_id, id",
        )

        if not linked_invoice_lines:
            return result

        linked_bills = linked_invoice_lines.mapped("move_id")

        all_bill_lines_domain = [
            ("move_id", "in", linked_bills.ids),
            (
                "move_id.move_type",
                "in",
                ("in_invoice", "in_refund"),
            ),
            ("display_type", "=", "product"),
        ]

        if not include_cancelled_bills:
            all_bill_lines_domain.append(
                ("move_id.state", "!=", "cancel")
            )

        all_bill_lines = self.env[
            "account.move.line"
        ].search(
            all_bill_lines_domain,
            order="move_id, id",
        )

        purchase_line_ids = set(purchase_lines.ids)
        first_purchase_line_by_bill = {}

        for linked_line in linked_invoice_lines:
            purchase_line = linked_line.purchase_line_id
            bill_id = linked_line.move_id.id

            if (
                purchase_line
                and purchase_line.id in purchase_line_ids
                and bill_id not in first_purchase_line_by_bill
            ):
                first_purchase_line_by_bill[
                    bill_id
                ] = purchase_line.id

        for invoice_line in all_bill_lines:
            purchase_line = invoice_line.purchase_line_id

            if (
                purchase_line
                and purchase_line.id in purchase_line_ids
            ):
                result[purchase_line.id] |= invoice_line
                continue

            fallback_purchase_line_id = (
                first_purchase_line_by_bill.get(
                    invoice_line.move_id.id
                )
            )

            if fallback_purchase_line_id:
                result[
                    fallback_purchase_line_id
                ] |= invoice_line

        return result

    def _get_period_moves_by_purchase_line(
        self,
        qualifying_moves,
    ):
        result = defaultdict(
            lambda: self.env["stock.move"]
        )

        for move in qualifying_moves:
            if move.purchase_line_id:
                result[
                    move.purchase_line_id.id
                ] |= move

        return result

    def _prepare_receipt_rows(self, period_moves):
        default_datetime = datetime(1970, 1, 1)

        sorted_moves = period_moves.sorted(
            key=lambda move: (
                move.picking_id.date_done
                or default_datetime,
                move.picking_id.name or "",
                move.id,
            )
        )

        receipt_rows = []

        for move in sorted_moves:
            picking = move.picking_id
            effective_date = False

            if picking.date_done:
                effective_date = (
                    fields.Datetime.context_timestamp(
                        self,
                        picking.date_done,
                    ).replace(tzinfo=None)
                )

            receipt_rows.append({
                "receipt_number": picking.name or "",
                "effective_date": effective_date,
                "receipt_line_status": (
                    self._get_selection_label(
                        picking,
                        "state",
                    )
                ),
                "period_received_quantity": (
                    self._get_move_received_quantity(
                        move
                    )
                ),
            })

        return receipt_rows

    def _get_bill_total_company_currency(self, bill):
        if "amount_total_signed" in bill._fields:
            return abs(
                bill.amount_total_signed or 0.0
            )

        company_currency = bill.company_id.currency_id

        if bill.currency_id == company_currency:
            return abs(bill.amount_total or 0.0)

        conversion_date = (
            bill.invoice_date
            or bill.date
            or fields.Date.context_today(self)
        )

        converted_amount = bill.currency_id._convert(
            bill.amount_total,
            company_currency,
            bill.company_id,
            conversion_date,
        )

        return abs(converted_amount)

    def _get_bill_line_subtotal_company_currency(
        self,
        invoice_line,
    ):
        return abs(invoice_line.balance or 0.0)

    def _get_bill_line_unit_price_company_currency(
        self,
        invoice_line,
    ):
        quantity = abs(invoice_line.quantity or 0.0)

        if not quantity:
            return 0.0

        subtotal_company_currency = (
            self._get_bill_line_subtotal_company_currency(
                invoice_line
            )
        )

        return subtotal_company_currency / quantity

    def _prepare_bill_rows(
        self,
        invoice_lines,
        displayed_bill_total_ids,
    ):
        default_date = fields.Date.from_string(
            "1970-01-01"
        )

        sorted_invoice_lines = invoice_lines.sorted(
            key=lambda line: (
                line.move_id.invoice_date
                or default_date,
                line.move_id.name or "",
                line.move_id.id,
                line.id,
            )
        )

        bill_rows = []

        for invoice_line in sorted_invoice_lines:
            bill = invoice_line.move_id
            show_bill_total = (
                bill.id not in displayed_bill_total_ids
            )

            bill_rows.append({
                "bill_number": (
                    bill.name
                    or bill.ref
                    or ""
                ),
                "bill_partner": (
                    bill.partner_id.display_name
                    or ""
                ),
                "bill_total": (
                    self._get_bill_total_company_currency(
                        bill
                    )
                    if show_bill_total
                    else False
                ),
                "bill_date": (
                    bill.invoice_date or False
                ),
                "bill_status": (
                    self._get_selection_label(
                        bill,
                        "state",
                    )
                ),
                "bill_product": (
                    invoice_line.product_id.display_name
                    or ""
                ),
                "bill_label": (
                    invoice_line.name or ""
                ),
                "bill_quantity": abs(
                    invoice_line.quantity or 0.0
                ),
                "bill_uom": (
                    self._get_invoice_line_uom(
                        invoice_line
                    )
                ),
                "bill_secondary_quantity": (
                    self._get_secondary_quantity(
                        invoice_line
                    )
                ),
                "bill_secondary_uom": (
                    self._get_secondary_uom(
                        invoice_line
                    )
                ),
                "bill_unit_price": (
                    self._get_bill_line_unit_price_company_currency(
                        invoice_line
                    )
                ),
                "bill_line_subtotal": (
                    self._get_bill_line_subtotal_company_currency(
                        invoice_line
                    )
                ),
            })

            if show_bill_total:
                displayed_bill_total_ids.add(bill.id)

        return bill_rows

    def _prepare_report_lines(self, data):
        qualifying_moves = self.env["stock.move"].search(
            self._get_qualifying_move_domain(data),
            order="id",
        )

        qualifying_purchase_orders = (
            qualifying_moves.mapped(
                "purchase_line_id.order_id"
            )
        )

        if not qualifying_purchase_orders:
            return []

        default_datetime = datetime(1970, 1, 1)

        purchase_orders = (
            qualifying_purchase_orders.sorted(
                key=lambda order: (
                    order.date_order
                    or default_datetime,
                    order.name or "",
                    order.id,
                )
            )
        )

        purchase_lines = purchase_orders.mapped(
            "order_line"
        ).filtered(
            lambda line: not line.display_type
        )

        invoice_lines_by_purchase_line = (
            self._get_invoice_lines_by_purchase_line(
                purchase_lines,
                include_cancelled_bills=data.get(
                    "include_cancelled_bills",
                    False,
                ),
            )
        )

        period_moves_by_purchase_line = (
            self._get_period_moves_by_purchase_line(
                qualifying_moves
            )
        )

        lines = []
        displayed_bill_total_ids = set()

        for purchase_order in purchase_orders:
            branch = self._get_purchase_branch(
                purchase_order
            )

            order_lines = (
                purchase_order.order_line.filtered(
                    lambda line: not line.display_type
                ).sorted(
                    key=lambda line: (
                        line.sequence,
                        line.id,
                    )
                )
            )

            first_order_row = True

            for purchase_line in order_lines:
                receipt_rows = (
                    self._prepare_receipt_rows(
                        period_moves_by_purchase_line[
                            purchase_line.id
                        ]
                    )
                )

                bill_rows = self._prepare_bill_rows(
                    invoice_lines_by_purchase_line[
                        purchase_line.id
                    ],
                    displayed_bill_total_ids,
                )

                if not receipt_rows:
                    receipt_rows = [None]

                if not bill_rows:
                    bill_rows = [None]

                discount = (
                    purchase_line.discount
                    if "discount"
                    in purchase_line._fields
                    else 0.0
                )

                discounted_unit_price = (
                    purchase_line.price_unit
                    * (
                        1.0
                        - discount / 100.0
                    )
                )

                first_purchase_line_row = True

                for receipt_row, bill_row in zip_longest(
                    receipt_rows,
                    bill_rows,
                    fillvalue=None,
                ):
                    period_received_quantity = (
                        receipt_row[
                            "period_received_quantity"
                        ]
                        if receipt_row
                        else 0.0
                    )

                    received_value = (
                        period_received_quantity
                        * discounted_unit_price
                    )

                    lines.append({
                        "branch": (
                            branch.display_name
                            if branch
                            else ""
                        ),
                        "order_reference": (
                            purchase_order.name or ""
                        ),
                        "created_on": (
                            purchase_order.create_date
                        ),
                        "confirmation_date": (
                            self._get_purchase_confirmation_date(
                                purchase_order
                            )
                        ),
                        "vendor": (
                            purchase_order.partner_id.display_name
                            or ""
                        ),
                        "purchase_total": (
                            purchase_order.amount_total
                            if first_order_row
                            else False
                        ),
                        "po_currency": (
                            purchase_order.currency_id.name
                            if first_order_row
                            else ""
                        ),
                        "purchase_total_company_currency": (
                            self._get_purchase_total_company_currency(
                                purchase_order
                            )
                            if first_order_row
                            else False
                        ),
                        "order_status": (
                            self._get_selection_label(
                                purchase_order,
                                "state",
                            )
                        ),
                        "billing_status": (
                            self._get_selection_label(
                                purchase_order,
                                "invoice_status",
                            )
                        ),
                        "receipt_status": (
                            self._get_purchase_receipt_status(
                                purchase_order
                            )
                        ),
                        "product": (
                            purchase_line.product_id.display_name
                            or ""
                        ),
                        "product_type": (
                            self._get_product_type(
                                purchase_line
                            )
                        ),
                        "description": (
                            purchase_line.name or ""
                        ),
                        "ordered_quantity": (
                            purchase_line.product_qty
                            if first_purchase_line_row
                            else False
                        ),
                        "purchase_uom": (
                            self._get_purchase_line_uom(
                                purchase_line
                            )
                            if first_purchase_line_row
                            else ""
                        ),
                        "purchase_secondary_quantity": (
                            self._get_secondary_quantity(
                                purchase_line
                            )
                            if first_purchase_line_row
                            else False
                        ),
                        "purchase_secondary_uom": (
                            self._get_secondary_uom(
                                purchase_line
                            )
                            if first_purchase_line_row
                            else ""
                        ),
                        "unit_price": (
                            purchase_line.price_unit
                            if first_purchase_line_row
                            else False
                        ),
                        "discount": (
                            discount
                            if first_purchase_line_row
                            else False
                        ),
                        "to_invoice_quantity": (
                            purchase_line.qty_to_invoice
                            if first_purchase_line_row
                            else False
                        ),
                        "total_received_quantity": (
                            purchase_line.qty_received
                            if first_purchase_line_row
                            else False
                        ),
                        "period_received_quantity": (
                            period_received_quantity
                            if receipt_row
                            else False
                        ),
                        "billed_quantity": (
                            purchase_line.qty_invoiced
                            if first_purchase_line_row
                            else False
                        ),
                        "line_subtotal": (
                            purchase_line.price_subtotal
                            if first_purchase_line_row
                            else False
                        ),
                        "receipt_number": (
                            receipt_row[
                                "receipt_number"
                            ]
                            if receipt_row
                            else ""
                        ),
                        "effective_date": (
                            receipt_row[
                                "effective_date"
                            ]
                            if receipt_row
                            else False
                        ),
                        "receipt_line_status": (
                            receipt_row[
                                "receipt_line_status"
                            ]
                            if receipt_row
                            else ""
                        ),
                        "received_value": (
                            received_value
                            if receipt_row
                            else False
                        ),
                        "bill_number": (
                            bill_row["bill_number"]
                            if bill_row
                            else ""
                        ),
                        "bill_partner": (
                            bill_row["bill_partner"]
                            if bill_row
                            else ""
                        ),
                        "bill_total": (
                            bill_row["bill_total"]
                            if bill_row
                            else False
                        ),
                        "bill_date": (
                            bill_row["bill_date"]
                            if bill_row
                            else False
                        ),
                        "bill_status": (
                            bill_row["bill_status"]
                            if bill_row
                            else ""
                        ),
                        "bill_product": (
                            bill_row["bill_product"]
                            if bill_row
                            else ""
                        ),
                        "bill_label": (
                            bill_row["bill_label"]
                            if bill_row
                            else ""
                        ),
                        "bill_quantity": (
                            bill_row["bill_quantity"]
                            if bill_row
                            else False
                        ),
                        "bill_uom": (
                            bill_row["bill_uom"]
                            if bill_row
                            else ""
                        ),
                        "bill_secondary_quantity": (
                            bill_row[
                                "bill_secondary_quantity"
                            ]
                            if bill_row
                            else False
                        ),
                        "bill_secondary_uom": (
                            bill_row[
                                "bill_secondary_uom"
                            ]
                            if bill_row
                            else ""
                        ),
                        "bill_unit_price": (
                            bill_row["bill_unit_price"]
                            if bill_row
                            else False
                        ),
                        "bill_line_subtotal": (
                            bill_row[
                                "bill_line_subtotal"
                            ]
                            if bill_row
                            else False
                        ),
                    })

                    first_order_row = False
                    first_purchase_line_row = False

        return lines

    def _write_number_or_blank(
        self,
        sheet,
        row,
        column,
        value,
        cell_format,
    ):
        if value is False or value is None:
            sheet.write(
                row,
                column,
                "",
                cell_format,
            )
            return

        sheet.write_number(
            row,
            column,
            value,
            cell_format,
        )

    def _write_datetime_or_blank(
        self,
        sheet,
        row,
        column,
        value,
        cell_format,
        blank_format,
    ):
        if not value:
            sheet.write(
                row,
                column,
                "",
                blank_format,
            )
            return

        datetime_value = (
            value
            if isinstance(value, datetime)
            else fields.Datetime.to_datetime(value)
        )

        if datetime_value.tzinfo:
            datetime_value = datetime_value.replace(
                tzinfo=None
            )

        sheet.write_datetime(
            row,
            column,
            datetime_value,
            cell_format,
        )

    def _write_total_row_cells(
        self,
        sheet,
        row,
        total_values,
        text_format,
        number_format,
        column_count,
    ):
        for column_index in range(column_count):
            value = total_values.get(column_index)

            if value is None:
                sheet.write(
                    row,
                    column_index,
                    "",
                    text_format,
                )
            elif isinstance(value, str):
                sheet.write(
                    row,
                    column_index,
                    value,
                    text_format,
                )
            else:
                sheet.write_number(
                    row,
                    column_index,
                    value,
                    number_format,
                )

    def generate_xlsx_report(
        self,
        workbook,
        data,
        wizard,
    ):
        wizard.ensure_one()

        sheet = workbook.add_worksheet(
            _("Purchase Excel Report")
        )

        last_column = 41

        sheet.freeze_panes(3, 0)
        sheet.autofilter(
            2,
            0,
            2,
            last_column,
        )
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.repeat_rows(2)
        sheet.set_margins(
            left=0.25,
            right=0.25,
            top=0.50,
            bottom=0.50,
        )

        title_format = workbook.add_format({
            "bold": True,
            "font_size": 18,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#1F4E78",
            "font_color": "#FFFFFF",
            "border": 1,
        })

        purchase_group_format = workbook.add_format({
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#5B9BD5",
            "font_color": "#FFFFFF",
            "border": 1,
        })

        line_group_format = workbook.add_format({
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#70AD47",
            "font_color": "#FFFFFF",
            "border": 1,
        })

        receipt_group_format = workbook.add_format({
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#ED7D31",
            "font_color": "#FFFFFF",
            "border": 1,
        })

        bill_group_format = workbook.add_format({
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#A5A5A5",
            "font_color": "#FFFFFF",
            "border": 1,
        })

        header_format = workbook.add_format({
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
            "bg_color": "#D9E1F2",
            "border": 1,
        })

        text_format = workbook.add_format({
            "align": "left",
            "valign": "top",
            "border": 1,
        })

        wrapped_text_format = workbook.add_format({
            "align": "left",
            "valign": "top",
            "text_wrap": True,
            "border": 1,
        })

        center_format = workbook.add_format({
            "align": "center",
            "valign": "top",
            "border": 1,
        })

        datetime_format = workbook.add_format({
            "num_format": "dd/mm/yyyy hh:mm",
            "align": "center",
            "valign": "top",
            "border": 1,
        })

        date_format = workbook.add_format({
            "num_format": "dd/mm/yyyy",
            "align": "center",
            "valign": "top",
            "border": 1,
        })

        quantity_format = workbook.add_format({
            "num_format": "#,##0.00",
            "align": "right",
            "valign": "top",
            "border": 1,
        })

        amount_format = workbook.add_format({
            "num_format": "#,##0.00",
            "align": "right",
            "valign": "top",
            "border": 1,
        })

        percentage_format = workbook.add_format({
            "num_format": "0.00",
            "align": "right",
            "valign": "top",
            "border": 1,
        })

        total_text_format = workbook.add_format({
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#D9EAD3",
            "border": 1,
        })

        total_number_format = workbook.add_format({
            "bold": True,
            "num_format": "#,##0.00",
            "align": "right",
            "valign": "vcenter",
            "bg_color": "#D9EAD3",
            "border": 1,
        })

        no_data_format = workbook.add_format({
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "font_color": "#C00000",
            "border": 1,
        })

        columns = [
            (_("Branch"), 18),
            (_("Order Reference"), 18),
            (_("Created On"), 18),
            (_("Confirmation Date"), 18),
            (_("Vendor"), 28),
            (_("Purchase Total"), 16),
            (_("PO Currency"), 14),
            (
                _("Purchase Total Company Currency"),
                26,
            ),
            (_("Order Status"), 16),
            (_("Billing Status"), 18),
            (_("Receipt Status"), 18),
            (_("Product"), 28),
            (_("Product Type"), 16),
            (_("Description"), 40),
            (_("Ordered Quantity"), 16),
            (_("UOM"), 16),
            (_("Secondary Quantity"), 18),
            (_("Secondary UOM"), 18),
            (_("Unit Price"), 15),
            (_("Discount (%)"), 14),
            (_("To Invoice Quantity"), 18),
            (_("Total Received Quantity"), 20),
            (_("Period Received Quantity"), 21),
            (_("Billed Quantity"), 16),
            (_("Line Subtotal"), 16),
            (_("Receipt Number"), 24),
            (_("Effective Date"), 20),
            (_("Receipt Line Status"), 18),
            (_("Received Value"), 16),
            (_("Bill Number"), 22),
            (_("Bill Partner"), 28),
            (_("Bill Total"), 18),
            (_("Bill Date"), 18),
            (_("Bill Status"), 18),
            (_("Invoice Line Product"), 30),
            (_("Invoice Line Label"), 38),
            (_("Invoice Line Quantity"), 22),
            (_("UOM"), 16),
            (_("Secondary Quantity"), 18),
            (_("Secondary UOM"), 18),
            (_("Invoice Line Unit Price"), 22),
            (_("Line Subtotal"), 18),
        ]

        for column_index, column in enumerate(columns):
            sheet.set_column(
                column_index,
                column_index,
                column[1],
            )

        sheet.set_row(0, 30)
        sheet.set_row(1, 24)
        sheet.set_row(2, 38)

        sheet.merge_range(
            0,
            0,
            0,
            last_column,
            _("Purchase Excel Report"),
            title_format,
        )

        sheet.merge_range(
            1,
            0,
            1,
            10,
            _("Purchase Orders"),
            purchase_group_format,
        )

        sheet.merge_range(
            1,
            11,
            1,
            24,
            _("Purchase Order Lines"),
            line_group_format,
        )

        sheet.merge_range(
            1,
            25,
            1,
            28,
            _("Receipts"),
            receipt_group_format,
        )

        sheet.merge_range(
            1,
            29,
            1,
            last_column,
            _("Vendor Bills - Company Currency"),
            bill_group_format,
        )

        for column_index, column in enumerate(columns):
            sheet.write(
                2,
                column_index,
                column[0],
                header_format,
            )

        report_lines = self._prepare_report_lines(data)
        row = 3

        if not report_lines:
            sheet.merge_range(
                row,
                0,
                row + 2,
                last_column,
                _(
                    "No purchase orders with completed receipts "
                    "were found for the selected effective date period."
                ),
                no_data_format,
            )
            return

        total_purchase_total = 0.0
        total_purchase_company_currency = 0.0
        total_ordered_quantity = 0.0
        total_purchase_secondary_quantity = 0.0
        total_to_invoice_quantity = 0.0
        total_received_quantity = 0.0
        total_period_received_quantity = 0.0
        total_billed_quantity = 0.0
        total_purchase_line_subtotal = 0.0
        total_received_value = 0.0
        total_bill_total = 0.0
        total_bill_line_quantity = 0.0
        total_bill_secondary_quantity = 0.0
        total_bill_line_subtotal = 0.0

        for line in report_lines:
            if line["purchase_total"] is not False:
                total_purchase_total += line[
                    "purchase_total"
                ]

            if (
                line[
                    "purchase_total_company_currency"
                ]
                is not False
            ):
                total_purchase_company_currency += line[
                    "purchase_total_company_currency"
                ]

            if line["ordered_quantity"] is not False:
                total_ordered_quantity += line[
                    "ordered_quantity"
                ]

            if (
                line[
                    "purchase_secondary_quantity"
                ]
                is not False
            ):
                total_purchase_secondary_quantity += line[
                    "purchase_secondary_quantity"
                ]

            if line["to_invoice_quantity"] is not False:
                total_to_invoice_quantity += line[
                    "to_invoice_quantity"
                ]

            if (
                line["total_received_quantity"]
                is not False
            ):
                total_received_quantity += line[
                    "total_received_quantity"
                ]

            if (
                line["period_received_quantity"]
                is not False
            ):
                total_period_received_quantity += line[
                    "period_received_quantity"
                ]

            if line["billed_quantity"] is not False:
                total_billed_quantity += line[
                    "billed_quantity"
                ]

            if line["line_subtotal"] is not False:
                total_purchase_line_subtotal += line[
                    "line_subtotal"
                ]

            if line["received_value"] is not False:
                total_received_value += line[
                    "received_value"
                ]

            if line["bill_total"] is not False:
                total_bill_total += line["bill_total"]

            if line["bill_quantity"] is not False:
                total_bill_line_quantity += line[
                    "bill_quantity"
                ]

            if (
                line["bill_secondary_quantity"]
                is not False
            ):
                total_bill_secondary_quantity += line[
                    "bill_secondary_quantity"
                ]

            if (
                line["bill_line_subtotal"]
                is not False
            ):
                total_bill_line_subtotal += line[
                    "bill_line_subtotal"
                ]

            sheet.write(
                row,
                0,
                line["branch"],
                text_format,
            )

            sheet.write(
                row,
                1,
                line["order_reference"],
                center_format,
            )

            if line["created_on"]:
                created_on = (
                    fields.Datetime.context_timestamp(
                        self,
                        line["created_on"],
                    ).replace(tzinfo=None)
                )

                sheet.write_datetime(
                    row,
                    2,
                    created_on,
                    datetime_format,
                )
            else:
                sheet.write(
                    row,
                    2,
                    "",
                    center_format,
                )

            if line["confirmation_date"]:
                confirmation_date = (
                    fields.Datetime.context_timestamp(
                        self,
                        line["confirmation_date"],
                    ).replace(tzinfo=None)
                )

                sheet.write_datetime(
                    row,
                    3,
                    confirmation_date,
                    datetime_format,
                )
            else:
                sheet.write(
                    row,
                    3,
                    "",
                    center_format,
                )

            sheet.write(
                row,
                4,
                line["vendor"],
                text_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                5,
                line["purchase_total"],
                amount_format,
            )

            sheet.write(
                row,
                6,
                line["po_currency"],
                center_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                7,
                line[
                    "purchase_total_company_currency"
                ],
                amount_format,
            )

            sheet.write(
                row,
                8,
                line["order_status"],
                center_format,
            )

            sheet.write(
                row,
                9,
                line["billing_status"],
                center_format,
            )

            sheet.write(
                row,
                10,
                line["receipt_status"],
                center_format,
            )

            sheet.write(
                row,
                11,
                line["product"],
                wrapped_text_format,
            )

            sheet.write(
                row,
                12,
                line["product_type"],
                center_format,
            )

            sheet.write(
                row,
                13,
                line["description"],
                wrapped_text_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                14,
                line["ordered_quantity"],
                quantity_format,
            )

            sheet.write(
                row,
                15,
                line["purchase_uom"],
                center_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                16,
                line[
                    "purchase_secondary_quantity"
                ],
                quantity_format,
            )

            sheet.write(
                row,
                17,
                line["purchase_secondary_uom"],
                center_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                18,
                line["unit_price"],
                amount_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                19,
                line["discount"],
                percentage_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                20,
                line["to_invoice_quantity"],
                quantity_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                21,
                line[
                    "total_received_quantity"
                ],
                quantity_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                22,
                line[
                    "period_received_quantity"
                ],
                quantity_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                23,
                line["billed_quantity"],
                quantity_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                24,
                line["line_subtotal"],
                amount_format,
            )

            sheet.write(
                row,
                25,
                line["receipt_number"],
                center_format,
            )

            self._write_datetime_or_blank(
                sheet,
                row,
                26,
                line["effective_date"],
                datetime_format,
                center_format,
            )

            sheet.write(
                row,
                27,
                line["receipt_line_status"],
                center_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                28,
                line["received_value"],
                amount_format,
            )

            sheet.write(
                row,
                29,
                line["bill_number"],
                center_format,
            )

            sheet.write(
                row,
                30,
                line["bill_partner"],
                text_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                31,
                line["bill_total"],
                amount_format,
            )

            if line["bill_date"]:
                sheet.write_datetime(
                    row,
                    32,
                    datetime.combine(
                        line["bill_date"],
                        datetime.min.time(),
                    ),
                    date_format,
                )
            else:
                sheet.write(
                    row,
                    32,
                    "",
                    center_format,
                )

            sheet.write(
                row,
                33,
                line["bill_status"],
                center_format,
            )

            sheet.write(
                row,
                34,
                line["bill_product"],
                wrapped_text_format,
            )

            sheet.write(
                row,
                35,
                line["bill_label"],
                wrapped_text_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                36,
                line["bill_quantity"],
                quantity_format,
            )

            sheet.write(
                row,
                37,
                line["bill_uom"],
                center_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                38,
                line[
                    "bill_secondary_quantity"
                ],
                quantity_format,
            )

            sheet.write(
                row,
                39,
                line["bill_secondary_uom"],
                center_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                40,
                line["bill_unit_price"],
                amount_format,
            )

            self._write_number_or_blank(
                sheet,
                row,
                41,
                line["bill_line_subtotal"],
                amount_format,
            )

            sheet.set_row(row, 22)
            row += 1

        total_values = {
            0: _("Total"),
            5: total_purchase_total,
            7: total_purchase_company_currency,
            14: total_ordered_quantity,
            16: total_purchase_secondary_quantity,
            20: total_to_invoice_quantity,
            21: total_received_quantity,
            22: total_period_received_quantity,
            23: total_billed_quantity,
            24: total_purchase_line_subtotal,
            28: total_received_value,
            31: total_bill_total,
            36: total_bill_line_quantity,
            38: total_bill_secondary_quantity,
            41: total_bill_line_subtotal,
        }

        self._write_total_row_cells(
            sheet,
            row,
            total_values,
            total_text_format,
            total_number_format,
            len(columns),
        )