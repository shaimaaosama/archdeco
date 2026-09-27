/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import {
    Component,
    onMounted,
    onWillStart,
    onWillUnmount,
    useState,
} from "@odoo/owl";

export class ProjectStatusUBRDashboard extends Component {
    static template =
        "project_status_ubr_dashboard.ProjectStatusUBRDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            loading: true,
            openDropdown: false,

            options: {
                projects: [],
                statuses: [],
                branches: [],
                partners: [],
                branch_label: "Branch",
                currency: {},
            },

            filters: {
                project_ids: [],
                status_ids: [],
                branch_ids: [],
                partner_ids: [],
                date_from: "",
                date_to: "",
            },

            search: {
                projects: "",
                partners: "",
            },

            rows: [],
            totals: {},
            count: 0,
        });

        this.closeDropdownsFromOutside =
            this.closeDropdownsFromOutside.bind(this);

        onWillStart(async () => {
            await this.loadInitialData();
        });

        onMounted(() => {
            document.addEventListener(
                "click",
                this.closeDropdownsFromOutside
            );
        });

        onWillUnmount(() => {
            document.removeEventListener(
                "click",
                this.closeDropdownsFromOutside
            );
        });
    }

    closeDropdownsFromOutside(event) {
        if (
            !event.target.closest(
                ".o_project_ubr_multi_dropdown"
            )
        ) {
            this.state.openDropdown = false;
        }
    }

    toggleDropdown(dropdownName, event) {
        if (event) {
            event.stopPropagation();
        }

        this.state.openDropdown =
            this.state.openDropdown === dropdownName
                ? false
                : dropdownName;
    }

    isDropdownOpen(dropdownName) {
        return (
            this.state.openDropdown === dropdownName
        );
    }

    toggleMultiOption(
        filterField,
        optionId,
        event
    ) {
        if (event) {
            event.stopPropagation();
        }

        const currentValues = [
            ...this.state.filters[filterField],
        ];

        const numericId = Number(optionId);
        const index = currentValues.indexOf(
            numericId
        );

        if (index >= 0) {
            currentValues.splice(index, 1);
        } else {
            currentValues.push(numericId);
        }

        this.state.filters[filterField] =
            currentValues;
    }

    isOptionSelected(filterField, optionId) {
        return this.state.filters[
            filterField
        ].includes(Number(optionId));
    }

    clearMultiFilter(filterField, event) {
        if (event) {
            event.stopPropagation();
        }

        this.state.filters[filterField] = [];
    }

    getSelectedCount(filterField) {
        return (
            this.state.filters[filterField]
                ?.length || 0
        );
    }

    getSelectedText(
        filterField,
        options,
        defaultText
    ) {
        const selectedIds =
            this.state.filters[filterField] || [];

        if (!selectedIds.length) {
            return defaultText;
        }

        const selectedOptions = options.filter(
            (option) =>
                selectedIds.includes(
                    Number(option.id)
                )
        );

        if (selectedOptions.length === 1) {
            return selectedOptions[0].name;
        }

        return `${selectedOptions.length} selected`;
    }

    updateDropdownSearch(searchField, event) {
        this.state.search[searchField] =
            event.target.value || "";
    }

    clearDropdownSearch(searchField, event) {
        if (event) {
            event.stopPropagation();
        }

        this.state.search[searchField] = "";
    }

    getFilteredProjects() {
        const searchValue = (
            this.state.search.projects || ""
        )
            .trim()
            .toLowerCase();

        if (!searchValue) {
            return this.state.options.projects;
        }

        return this.state.options.projects.filter(
            (project) =>
                (project.name || "")
                    .toLowerCase()
                    .includes(searchValue)
        );
    }

    getFilteredPartners() {
        const searchValue = (
            this.state.search.partners || ""
        )
            .trim()
            .toLowerCase();

        if (!searchValue) {
            return this.state.options.partners;
        }

        return this.state.options.partners.filter(
            (partner) =>
                (partner.name || "")
                    .toLowerCase()
                    .includes(searchValue)
        );
    }

    async loadInitialData() {
        this.state.loading = true;

        try {
            const result = await this.orm.call(
                "project.status.ubr.dashboard",
                "get_initial_data",
                [
                    this.cleanFilters(),
                ]
            );

            this.state.options = result.options || {
                projects: [],
                statuses: [],
                branches: [],
                partners: [],
                branch_label: "Branch",
                currency: {},
            };

            this.state.rows =
                result.data?.rows || [];

            this.state.totals =
                result.data?.totals || {};

            this.state.count =
                result.data?.count || 0;
        } catch (error) {
            console.error(
                "Project Status & UBR initial load error:",
                error
            );

            this.notification.add(
                this.getErrorMessage(
                    error,
                    "Unable to load dashboard data."
                ),
                {
                    type: "danger",
                }
            );
        } finally {
            this.state.loading = false;
        }
    }

    async loadData() {
        this.state.loading = true;
        this.state.openDropdown = false;

        try {
            const result = await this.orm.call(
                "project.status.ubr.dashboard",
                "get_dashboard_data",
                [
                    this.cleanFilters(),
                ]
            );

            this.state.rows =
                result.rows || [];

            this.state.totals =
                result.totals || {};

            this.state.count =
                result.count || 0;
        } catch (error) {
            console.error(
                "Project Status & UBR data load error:",
                error
            );

            this.notification.add(
                this.getErrorMessage(
                    error,
                    "Unable to load dashboard data."
                ),
                {
                    type: "danger",
                }
            );
        } finally {
            this.state.loading = false;
        }
    }

    cleanFilters() {
        return {
            project_ids: [
                ...this.state.filters.project_ids,
            ],
            status_ids: [
                ...this.state.filters.status_ids,
            ],
            branch_ids: [
                ...this.state.filters.branch_ids,
            ],
            partner_ids: [
                ...this.state.filters.partner_ids,
            ],
            date_from:
                this.state.filters.date_from
                || false,
            date_to:
                this.state.filters.date_to
                || false,
        };
    }

    updateDate(field, event) {
        this.state.filters[field] =
            event.target.value;
    }

    async applyFilters() {
        const dateFrom =
            this.state.filters.date_from;

        const dateTo =
            this.state.filters.date_to;

        if (
            dateFrom
            && dateTo
            && dateFrom > dateTo
        ) {
            this.notification.add(
                "Date From cannot be later than Date To.",
                {
                    type: "warning",
                }
            );

            return;
        }

        await this.loadData();
    }

    async resetFilters() {
        this.state.filters.project_ids = [];
        this.state.filters.status_ids = [];
        this.state.filters.branch_ids = [];
        this.state.filters.partner_ids = [];
        this.state.filters.date_from = "";
        this.state.filters.date_to = "";

        this.state.search.projects = "";
        this.state.search.partners = "";

        this.state.openDropdown = false;

        await this.loadData();
    }

    exportExcel() {
        const filters = encodeURIComponent(
            JSON.stringify(
                this.cleanFilters()
            )
        );

        window.location.href =
            `/project_status_ubr/export_xlsx`
            + `?filters=${filters}`;
    }

    async openSaleOrder(row, saleOrderName) {
        if (
            !row
            || !row.project_id
            || !saleOrderName
        ) {
            this.notification.add(
                "The sales order is not available.",
                {
                    type: "warning",
                }
            );

            return;
        }

        try {
            const orders = await this.orm.searchRead(
                "sale.order",
                [
                    [
                        "project_id",
                        "=",
                        Number(row.project_id),
                    ],
                    [
                        "name",
                        "=",
                        saleOrderName,
                    ],
                    [
                        "state",
                        "in",
                        ["sale", "done"],
                    ],
                ],
                [
                    "id",
                    "name",
                ],
                {
                    limit: 1,
                }
            );

            if (!orders.length) {
                this.notification.add(
                    `Sales Order ${saleOrderName} was not found.`,
                    {
                        type: "warning",
                    }
                );

                return;
            }

            await this.action.doAction({
                type: "ir.actions.act_window",
                name: saleOrderName,
                res_model: "sale.order",
                res_id: orders[0].id,
                views: [
                    [false, "form"],
                ],
                view_mode: "form",
                target: "current",
            });
        } catch (error) {
            console.error(
                "Project Status & UBR open sale order error:",
                error
            );

            this.notification.add(
                this.getErrorMessage(
                    error,
                    "Unable to open the sales order."
                ),
                {
                    type: "danger",
                }
            );
        }
    }

    async openSalesOrders(row) {
        if (!row || !row.project_id) {
            this.notification.add(
                "The project is not available for this row.",
                {
                    type: "warning",
                }
            );

            return;
        }

        const domain = [
            [
                "project_id",
                "=",
                Number(row.project_id),
            ],
            [
                "state",
                "in",
                ["sale", "done"],
            ],
        ];

        if (
            this.state.filters.partner_ids
            && this.state.filters.partner_ids.length
        ) {
            domain.push([
                "partner_id",
                "in",
                [
                    ...this.state.filters.partner_ids,
                ],
            ]);
        }

        if (this.state.filters.date_from) {
            domain.push([
                "date_order",
                ">=",
                `${this.state.filters.date_from} 00:00:00`,
            ]);
        }

        if (this.state.filters.date_to) {
            domain.push([
                "date_order",
                "<=",
                `${this.state.filters.date_to} 23:59:59`,
            ]);
        }

        try {
            await this.action.doAction({
                type: "ir.actions.act_window",
                name: `Sales Orders - ${row.project || ""}`,
                res_model: "sale.order",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                view_mode: "list,form",
                domain: domain,
                target: "current",
                context: {
                    create: false,
                },
            });
        } catch (error) {
            console.error(
                "Project Status & UBR open sales orders error:",
                error
            );

            this.notification.add(
                this.getErrorMessage(
                    error,
                    "Unable to open sales orders."
                ),
                {
                    type: "danger",
                }
            );
        }
    }

    async openExpectedExpenseSalesOrders(row) {
        if (!row || !row.project_id) {
            this.notification.add(
                "The project is not available for this row.",
                {
                    type: "warning",
                }
            );

            return;
        }

        try {
            await this.action.doAction({
                type: "ir.actions.act_window",
                name:
                    `Expected Expense Sales Orders - `
                    + `${row.project || ""}`,
                res_model: "sale.order",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                view_mode: "list,form",
                domain: [
                    [
                        "project_id",
                        "=",
                        Number(row.project_id),
                    ],
                    [
                        "state",
                        "in",
                        ["sale", "done"],
                    ],
                ],
                target: "current",
                context: {
                    create: false,
                },
            });
        } catch (error) {
            console.error(
                "Project Status & UBR expected expense "
                + "sales orders error:",
                error
            );

            this.notification.add(
                this.getErrorMessage(
                    error,
                    "Unable to open expected expense "
                    + "Sales Orders."
                ),
                {
                    type: "danger",
                }
            );
        }
    }

    async openJournalItems(row, metric) {
        if (!row || !row.project_id) {
            this.notification.add(
                "The project is not available for this row.",
                {
                    type: "warning",
                }
            );

            return;
        }

        try {
            const action = await this.orm.call(
                "project.status.ubr.dashboard",
                "action_open_journal_items",
                [
                    Number(row.project_id),
                    metric,
                    this.state.filters.date_from
                        || false,
                    this.state.filters.date_to
                        || false,
                ]
            );

            if (!action) {
                this.notification.add(
                    "No journal item action was returned.",
                    {
                        type: "warning",
                    }
                );

                return;
            }

            if (!Array.isArray(action.views)) {
                action.views = [
                    [false, "list"],
                    [false, "form"],
                ];
            }

            if (!Array.isArray(action.domain)) {
                action.domain = [];
            }

            if (
                !action.context
                || typeof action.context !== "object"
            ) {
                action.context = {};
            }

            action.view_mode =
                action.view_mode || "list,form";

            action.target =
                action.target || "current";

            await this.action.doAction(action);
        } catch (error) {
            console.error(
                "Project Status & UBR journal items error:",
                error
            );

            this.notification.add(
                this.getErrorMessage(
                    error,
                    "Unable to open journal items."
                ),
                {
                    type: "danger",
                }
            );
        }
    }

    getErrorMessage(error, fallbackMessage) {
        return (
            error?.data?.message
            || error?.data?.arguments?.[0]
            || error?.message
            || fallbackMessage
        );
    }

    formatAmount(value) {
        const currency =
            this.state.options.currency || {};

        const decimals =
            currency.decimal_places ?? 2;

        const amount = new Intl.NumberFormat(
            undefined,
            {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals,
            }
        ).format(
            Number(value || 0)
        );

        if (!currency.symbol) {
            return amount;
        }

        if (currency.position === "before") {
            return `${currency.symbol} ${amount}`;
        }

        return `${amount} ${currency.symbol}`;
    }

    formatPercentage(value) {
        return `${new Intl.NumberFormat(
            undefined,
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            }
        ).format(
            Number(value || 0) * 100
        )}%`;
    }

    percentageClass(value) {
        const percentage =
            Number(value || 0);

        if (percentage < 0) {
            return "is-negative";
        }

        if (percentage >= 0.3) {
            return "is-positive";
        }

        return "is-neutral";
    }
}

registry.category("actions").add(
    "project_status_ubr_dashboard",
    ProjectStatusUBRDashboard
);