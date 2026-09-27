/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";


class AccountBudgetDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.ubrRequestToken = 0;

        this.state = useState({
            loading: true,
            screen: "years",

            years: [],
            selectedYear: false,
            dateFrom: false,
            dateTo: false,
            pendingDateFrom: false,
            pendingDateTo: false,
            useUbrDates: false,

            selectedBudgetIds: null,
            pendingBudgetIds: null,

            yearDetails: {
                summary: {},
                budgets: [],
                available_budgets: [],
                selected_budget_ids: [],
            },

            selectedBudget: {
                id: false,
                included_branches: [],
                lines: [],
            },

            cinemaPopup: {
                open: false,
                title: "",
                budget_group_id: false,
                lines: [],
                total: 0,
            },
        });

        onWillStart(async () => {
            const params = (
                this.props.action
                && this.props.action.params
            ) ? this.props.action.params : {};

            if (params && params.budget_id) {
                await this.loadYears();

                this.state.selectedYear = params.year;
                this.state.dateFrom = params.date_from;
                this.state.dateTo = params.date_to;
                this.state.pendingDateFrom = params.date_from;
                this.state.pendingDateTo = params.date_to;
                this.state.useUbrDates = Boolean(params.use_ubr_dates);
                this.state.selectedBudgetIds = null;
                this.state.pendingBudgetIds = null;
                this.state.screen = "year";

                await this.loadYearDetails();
                await this.openBudget(
                    params.budget_id
                );
            } else {
                await this.loadYears();
            }
        });
    }

    async loadYears() {
        this.state.loading = true;

        try {
            this.state.years = await this.orm.call(
                "account.report.budget",
                "get_budget_dashboard_years",
                [],
                {}
            );
        } finally {
            this.state.loading = false;
        }
    }

    async openYear(year) {
        this.state.selectedYear = year;
        this.state.dateFrom = `${year}-01-01`;
        this.state.dateTo = `${year}-12-31`;
        this.state.pendingDateFrom = `${year}-01-01`;
        this.state.pendingDateTo = `${year}-12-31`;
        this.state.useUbrDates = false;

        this.state.selectedBudgetIds = null;
        this.state.pendingBudgetIds = null;

        this.state.screen = "year";

        await this.loadYearDetails();
    }

    async loadYearDetails() {
        this.state.loading = true;
        this.ubrRequestToken += 1;

        try {
            const budgetIds = (
                this.state.selectedBudgetIds === null
                    ? false
                    : [
                        ...this.state.selectedBudgetIds,
                    ]
            );

            const result = await this.orm.call(
                "account.report.budget",
                "get_budget_dashboard_year_details",
                [],
                {
                    year: (
                        this.state.selectedYear
                    ),
                    date_from: (
                        this.state.dateFrom
                    ),
                    date_to: (
                        this.state.dateTo
                    ),
                    budget_ids: budgetIds,
                }
            );

            this.state.yearDetails = {
                summary: (
                    result.summary || {}
                ),
                budgets: (
                    result.budgets || []
                ),
                available_budgets: (
                    result.available_budgets
                    || []
                ),
                selected_budget_ids: (
                    result.selected_budget_ids
                    || []
                ),
            };

            if (
                this.state.selectedBudgetIds
                === null
            ) {
                const defaultBudgetIds = [
                    ...(
                        result.selected_budget_ids
                        || []
                    ),
                ];

                this.state.selectedBudgetIds = [
                    ...defaultBudgetIds,
                ];

                this.state.pendingBudgetIds = [
                    ...defaultBudgetIds,
                ];
            }

            if (
                this.state.pendingBudgetIds
                === null
            ) {
                this.state.pendingBudgetIds = [
                    ...(
                        this.state.selectedBudgetIds
                        || []
                    ),
                ];
            }
        } finally {
            this.state.loading = false;
        }

        this.loadYearUbrValues();
    }

    async loadYearUbrValues() {
        if (
            this.state.screen !== "year"
            || !this.state.selectedYear
        ) {
            return;
        }

        const token = (
            this.ubrRequestToken
            + 1
        );

        this.ubrRequestToken = token;

        const year = this.state.selectedYear;
        const dateFrom = this.state.dateFrom;
        const dateTo = this.state.dateTo;
        const useUbrDates = this.state.useUbrDates;

        const budgetIds = (
            this.state.selectedBudgetIds === null
                ? false
                : [
                    ...this.state.selectedBudgetIds,
                ]
        );

        try {
            const result = await this.orm.call(
                "account.report.budget",
                "get_budget_dashboard_year_ubr_values",
                [],
                {
                    year: year,
                    date_from: (
                        useUbrDates
                            ? dateFrom
                            : false
                    ),
                    date_to: (
                        useUbrDates
                            ? dateTo
                            : false
                    ),
                    budget_ids: budgetIds,
                }
            );

            if (
                this.ubrRequestToken !== token
                || this.state.screen !== "year"
                || this.state.selectedYear !== year
                || this.state.dateFrom !== dateFrom
                || this.state.dateTo !== dateTo
                || this.state.useUbrDates !== useUbrDates
            ) {
                return;
            }

            const ubrByBudgetId = {};

            for (const row of result.budgets || []) {
                ubrByBudgetId[row.id] = (
                    row.ubr || 0
                );
            }

            const updatedBudgets = (
                this.state.yearDetails.budgets
                || []
            ).map((budget) => {
                return {
                    ...budget,
                    ubr: (
                        ubrByBudgetId[budget.id]
                        || 0
                    ),
                };
            });

            this.state.yearDetails = {
                ...this.state.yearDetails,
                summary: {
                    ...(
                        this.state.yearDetails.summary
                        || {}
                    ),
                    ubr: (
                        result.summary_ubr || 0
                    ),
                },
                budgets: updatedBudgets,
            };
        } catch (error) {
            console.warn(
                "Unable to load UBR values",
                error
            );
        }
    }

    isBudgetSelected(budgetId) {
        return (
            Array.isArray(
                this.state.pendingBudgetIds
            )
            && this.state.pendingBudgetIds.includes(
                budgetId
            )
        );
    }

    onBudgetSelectionChange(
        ev,
        budgetId
    ) {
        let pendingIds = Array.isArray(
            this.state.pendingBudgetIds
        )
            ? [
                ...this.state.pendingBudgetIds,
            ]
            : [];

        if (ev.target.checked) {
            if (
                !pendingIds.includes(
                    budgetId
                )
            ) {
                pendingIds.push(
                    budgetId
                );
            }
        } else {
            pendingIds = pendingIds.filter(
                (id) => id !== budgetId
            );
        }

        this.state.pendingBudgetIds = (
            pendingIds
        );
    }

    selectAllBudgets(ev) {
        if (ev) {
            ev.preventDefault();
            ev.stopPropagation();
        }

        this.state.pendingBudgetIds = (
            this.state.yearDetails
                .available_budgets
            || []
        ).map(
            (budget) => budget.id
        );
    }

    clearBudgetSelection(ev) {
        if (ev) {
            ev.preventDefault();
            ev.stopPropagation();
        }

        this.state.pendingBudgetIds = [];
    }

    async confirmBudgetSelection(ev) {
        if (ev) {
            ev.preventDefault();
            ev.stopPropagation();
        }

        const detailsElement = (
            ev
            && ev.currentTarget
        )
            ? ev.currentTarget.closest(
                ".budget_multi_select"
            )
            : null;

        this.state.selectedBudgetIds = (
            Array.isArray(
                this.state.pendingBudgetIds
            )
                ? [
                    ...this.state.pendingBudgetIds,
                ]
                : []
        );

        await this.loadYearDetails();

        this.state.pendingBudgetIds = [
            ...(
                this.state.selectedBudgetIds
                || []
            ),
        ];

        if (detailsElement) {
            detailsElement.open = false;
        }
    }

    cancelBudgetSelection(ev) {
        if (ev) {
            ev.preventDefault();
            ev.stopPropagation();
        }

        this.state.pendingBudgetIds = [
            ...(
                this.state.selectedBudgetIds
                || []
            ),
        ];

        const detailsElement = (
            ev
            && ev.currentTarget
        )
            ? ev.currentTarget.closest(
                ".budget_multi_select"
            )
            : null;

        if (detailsElement) {
            detailsElement.open = false;
        }
    }

    getBudgetSelectionLabel() {
        const availableBudgets = (
            this.state.yearDetails
                .available_budgets
            || []
        );

        const appliedIds = Array.isArray(
            this.state.selectedBudgetIds
        )
            ? this.state.selectedBudgetIds
            : [];

        if (!availableBudgets.length) {
            return "No Budgets Available";
        }

        if (
            appliedIds.length
            === availableBudgets.length
        ) {
            return (
                `All Budgets (${appliedIds.length})`
            );
        }

        if (!appliedIds.length) {
            return "No Budget Selected";
        }

        if (appliedIds.length === 1) {
            const selectedBudget = (
                availableBudgets.find(
                    (budget) => (
                        budget.id
                        === appliedIds[0]
                    )
                )
            );

            return selectedBudget
                ? selectedBudget.name
                : "1 Budget Selected";
        }

        return (
            `${appliedIds.length} Budgets Selected`
        );
    }

    getPendingBudgetSelectionLabel() {
        const pendingIds = Array.isArray(
            this.state.pendingBudgetIds
        )
            ? this.state.pendingBudgetIds
            : [];

        return (
            `${pendingIds.length} Selected`
        );
    }

    async openBudget(budgetId) {
        this.state.loading = true;

        try {
            const result = await this.orm.call(
                "account.report.budget",
                "get_budget_dashboard_budget_details",
                [],
                {
                    budget_id: budgetId,
                    date_from: (
                        this.state.dateFrom
                    ),
                    date_to: (
                        this.state.dateTo
                    ),
                    use_ubr_dates: (
                        this.state.useUbrDates
                    ),
                }
            );

            if (
                !result
                || !result.id
            ) {
                return;
            }

            this.state.selectedBudget = (
                result
            );

            this.state.screen = "budget";
        } finally {
            this.state.loading = false;
        }
    }

    async reloadSelectedBudget() {
        if (
            !this.state.selectedBudget
            || !this.state.selectedBudget.id
        ) {
            return;
        }

        this.state.loading = true;

        try {
            this.state.selectedBudget = (
                await this.orm.call(
                    "account.report.budget",
                    "get_budget_dashboard_budget_details",
                    [],
                    {
                        budget_id: (
                            this.state
                                .selectedBudget
                                .id
                        ),
                        date_from: (
                            this.state.dateFrom
                        ),
                        date_to: (
                            this.state.dateTo
                        ),
                        use_ubr_dates: (
                            this.state.useUbrDates
                        ),
                    }
                )
            );
        } finally {
            this.state.loading = false;
        }
    }

    onPendingDateFromChange(ev) {
        this.state.pendingDateFrom = (
            ev.target.value
        );
    }

    onPendingDateToChange(ev) {
        this.state.pendingDateTo = (
            ev.target.value
        );
    }

    async applyDateFilter() {
        if (
            !this.state.pendingDateFrom
            || !this.state.pendingDateTo
        ) {
            return;
        }

        if (
            this.state.pendingDateFrom
            > this.state.pendingDateTo
        ) {
            return;
        }

        this.state.dateFrom = (
            this.state.pendingDateFrom
        );

        this.state.dateTo = (
            this.state.pendingDateTo
        );

        this.state.useUbrDates = true;

        if (
            this.state.screen === "year"
        ) {
            await this.loadYearDetails();
        } else if (
            this.state.screen === "budget"
        ) {
            await this.reloadSelectedBudget();
        }
    }

    async openActualMoveLines(lineId) {
        const action = await this.orm.call(
            "account.report.budget",
            "action_open_budget_line_actual_move_lines",
            [],
            {
                budget_line_id: lineId,
                date_from: (
                    this.state.dateFrom
                ),
                date_to: (
                    this.state.dateTo
                ),
            }
        );

        if (action) {
            await this.action.doAction(
                action
            );
        }
    }

    openCinemaProductsInfo(line) {
        if (
            !this.state.selectedBudget.is_cinema_branch
            || !line.can_open_cinema_products
        ) {
            return;
        }

        this.state.cinemaPopup = {
            open: true,
            title: (
                line.budget_group_name
                || "Cinema Products"
            ),
            budget_group_id: (
                line.budget_group_id
                || false
            ),
            lines: (
                line.cinema_products_details
                || []
            ),
            total: (
                line.cinema_products_amount
                || 0
            ),
        };
    }

    closeCinemaProductsInfo() {
        this.state.cinemaPopup = {
            open: false,
            title: "",
            budget_group_id: false,
            lines: [],
            total: 0,
        };
    }

    async openCinemaProductJournalItems(row) {
        if (
            !this.state.selectedBudget.is_cinema_branch
            || !this.state.cinemaPopup.budget_group_id
            || !row.branch_id
        ) {
            return;
        }

        const action = await this.orm.call(
            "account.report.budget",
            "action_open_cinema_product_journal_items",
            [],
            {
                budget_id: (
                    this.state.selectedBudget.id
                ),
                budget_group_id: (
                    this.state.cinemaPopup.budget_group_id
                ),
                source_branch_id: (
                    row.branch_id
                ),
                date_from: (
                    this.state.dateFrom
                ),
                date_to: (
                    this.state.dateTo
                ),
            }
        );

        if (action) {
            await this.action.doAction(
                action
            );
        }
    }

    async backToYears() {
        this.state.screen = "years";
        this.state.selectedYear = false;
        this.state.dateFrom = false;
        this.state.dateTo = false;
        this.state.pendingDateFrom = false;
        this.state.pendingDateTo = false;
        this.state.useUbrDates = false;
        this.state.selectedBudgetIds = null;
        this.state.pendingBudgetIds = null;

        this.state.yearDetails = {
            summary: {},
            budgets: [],
            available_budgets: [],
            selected_budget_ids: [],
        };

        this.state.selectedBudget = {
            id: false,
            included_branches: [],
            lines: [],
        };

        this.closeCinemaProductsInfo();

        await this.loadYears();
    }

    async backToYear() {
        this.state.screen = "year";

        this.state.selectedBudget = {
            id: false,
            included_branches: [],
            lines: [],
        };

        this.state.pendingBudgetIds = [
            ...(
                this.state.selectedBudgetIds
                || []
            ),
        ];

        this.state.pendingDateFrom = (
            this.state.dateFrom
        );

        this.state.pendingDateTo = (
            this.state.dateTo
        );

        this.closeCinemaProductsInfo();

        await this.loadYearDetails();
    }

    formatAmount(value) {
        value = Number(
            value || 0
        );

        return new Intl.NumberFormat(
            "en-US",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            }
        ).format(value);
    }

    formatDate(value) {
        if (!value) {
            return "";
        }

        const parts = String(
            value
        ).split("-");

        if (parts.length === 3) {
            return (
                `${parts[1]}-${parts[2]}-${parts[0]}`
            );
        }

        return value;
    }

    isSalesBudget(planned) {
        return Number(
            planned || 0
        ) > 0;
    }

    isExpenseBudget(planned) {
        return Number(
            planned || 0
        ) < 0;
    }

    getIndicatorClass(
        planned,
        difference
    ) {
        planned = Number(
            planned || 0
        );

        difference = Number(
            difference || 0
        );

        if (difference === 0) {
            return "indicator_neutral";
        }

        if (
            this.isSalesBudget(planned)
        ) {
            return difference < 0
                ? "indicator_good"
                : "indicator_bad";
        }

        if (
            this.isExpenseBudget(planned)
        ) {
            return difference < 0
                ? "indicator_good"
                : "indicator_bad";
        }

        return "indicator_undefined";
    }

    getIndicatorLabel(
        planned,
        difference
    ) {
        planned = Number(
            planned || 0
        );

        difference = Number(
            difference || 0
        );

        if (difference === 0) {
            return "Balanced";
        }

        if (
            this.isSalesBudget(planned)
        ) {
            return difference < 0
                ? "Above Target"
                : "Under Target";
        }

        if (
            this.isExpenseBudget(planned)
        ) {
            return difference < 0
                ? "Under Budget"
                : "Over Budget";
        }

        return "Undefined";
    }

    getIndicatorIcon() {
        return "●";
    }

    getIndicatorTitle(
        planned,
        difference
    ) {
        planned = Number(
            planned || 0
        );

        difference = Number(
            difference || 0
        );

        if (difference === 0) {
            return (
                "Actual amount is exactly "
                + "matching the budget."
            );
        }

        if (
            this.isSalesBudget(planned)
        ) {
            return difference < 0
                ? (
                    "Sales actual is higher "
                    + "than the planned target."
                )
                : (
                    "Sales actual is lower "
                    + "than the planned target."
                );
        }

        if (
            this.isExpenseBudget(planned)
        ) {
            return difference < 0
                ? (
                    "Expense actual is lower "
                    + "than the planned budget."
                )
                : (
                    "Expense actual exceeded "
                    + "the planned budget."
                );
        }

        return (
            "Budget type cannot be defined "
            + "because planned amount is zero."
        );
    }

    getRowClass(
        planned,
        difference
    ) {
        const indicatorClass = (
            this.getIndicatorClass(
                planned,
                difference
            )
        );

        if (
            indicatorClass
            === "indicator_good"
        ) {
            return "budget_row_good";
        }

        if (
            indicatorClass
            === "indicator_bad"
        ) {
            return "budget_row_bad";
        }

        if (
            indicatorClass
            === "indicator_undefined"
        ) {
            return "budget_row_undefined";
        }

        return "budget_row_neutral";
    }

    getDifferenceTextClass(
        planned,
        difference
    ) {
        const indicatorClass = (
            this.getIndicatorClass(
                planned,
                difference
            )
        );

        if (
            indicatorClass
            === "indicator_good"
        ) {
            return "text_success";
        }

        if (
            indicatorClass
            === "indicator_bad"
        ) {
            return "text_warning";
        }

        if (
            indicatorClass
            === "indicator_undefined"
        ) {
            return "text_undefined";
        }

        return "muted_text";
    }

    getCinemaProductsTextClass(amount) {
        amount = Number(
            amount || 0
        );

        if (amount > 0) {
            return "text_success";
        }

        if (amount < 0) {
            return "text_warning";
        }

        return "muted_text";
    }

    getKpiClass(
        planned,
        difference
    ) {
        const indicatorClass = (
            this.getIndicatorClass(
                planned,
                difference
            )
        );

        if (
            indicatorClass
            === "indicator_good"
        ) {
            return "success";
        }

        if (
            indicatorClass
            === "indicator_bad"
        ) {
            return "warning";
        }

        if (
            indicatorClass
            === "indicator_undefined"
        ) {
            return "undefined";
        }

        return "neutral";
    }
}


AccountBudgetDashboard.template =
    "accounting_customs.AccountBudgetDashboard";


registry.category("actions").add(
    "account_budget_dashboard",
    AccountBudgetDashboard
);