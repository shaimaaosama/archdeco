/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const DETAILED_COLUMNS = [
    { key: "internal_reference", label: "Internal Reference", type: "text", total: false },
    { key: "product_name", label: "Product", type: "text", total: false },
    { key: "brand", label: "Brand", type: "text", total: false },
    { key: "category", label: "Product Category", type: "text", total: false },
    { key: "uom", label: "UOM", type: "text", total: false },
    { key: "warehouse", label: "Warehouse", type: "text", total: false },
    { key: "current_qty", label: "Current Qty", type: "number", total: true },
    { key: "current_value", label: "Current Value", type: "amount", total: true },
    { key: "closing_avg_cost", label: "Avg. Cost", type: "amount", total: false },
    { key: "oldest_stock_date", label: "Oldest Stock Date", type: "text", total: false },
    { key: "weighted_avg_age", label: "Avg. Age", type: "number", total: false },
    { key: "qty_0_30", label: "Period 1 Qty", type: "number", total: true, bucketIndex: 0, bucketType: "Qty" },
    { key: "value_0_30", label: "Period 1 Value", type: "amount", total: true, bucketIndex: 0, bucketType: "Value" },
    { key: "qty_31_60", label: "Period 2 Qty", type: "number", total: true, bucketIndex: 1, bucketType: "Qty" },
    { key: "value_31_60", label: "Period 2 Value", type: "amount", total: true, bucketIndex: 1, bucketType: "Value" },
    { key: "qty_61_90", label: "Period 3 Qty", type: "number", total: true, bucketIndex: 2, bucketType: "Qty" },
    { key: "value_61_90", label: "Period 3 Value", type: "amount", total: true, bucketIndex: 2, bucketType: "Value" },
    { key: "qty_91_180", label: "Period 4 Qty", type: "number", total: true, bucketIndex: 3, bucketType: "Qty" },
    { key: "value_91_180", label: "Period 4 Value", type: "amount", total: true, bucketIndex: 3, bucketType: "Value" },
    { key: "qty_181_365", label: "Period 5 Qty", type: "number", total: true, bucketIndex: 4, bucketType: "Qty" },
    { key: "value_181_365", label: "Period 5 Value", type: "amount", total: true, bucketIndex: 4, bucketType: "Value" },
    { key: "qty_over_365", label: "Period 6 Qty", type: "number", total: true, bucketIndex: 5, bucketType: "Qty" },
    { key: "value_over_365", label: "Period 6 Value", type: "amount", total: true, bucketIndex: 5, bucketType: "Value" },
    { key: "last_receipt_date", label: "Last Receipt", type: "text", total: false },
    { key: "last_issue_date", label: "Last Issue", type: "text", total: false },
    { key: "days_since_receipt", label: "Days Since Receipt", type: "number", total: false },
    { key: "days_since_issue", label: "Days Since Issue", type: "number", total: false },
    { key: "aged_qty_180", label: "Aged Qty", type: "number", total: true, dynamicType: "aged_qty" },
    { key: "aged_value_180", label: "Aged Value", type: "amount", total: true, dynamicType: "aged_value" },
    { key: "aged_percent_qty", label: "Aged % Qty", type: "percent", total: false, dynamicType: "aged_percent_qty" },
    { key: "aged_percent_value", label: "Aged % Value", type: "percent", total: false, dynamicType: "aged_percent_value" },
    { key: "qty_reconciliation", label: "Qty Reconciliation", type: "number", total: true },
    { key: "value_reconciliation", label: "Value Reconciliation", type: "amount", total: true },
    { key: "negative_stock_flag", label: "Negative Stock", type: "flag", total: false },
    { key: "no_movement_365", label: "No Movement", type: "flag", total: false, dynamicType: "no_movement" },
    { key: "aging_risk_level", label: "Risk Level", type: "risk", total: false },
];

const SUMMARY_COLUMNS = [
    { key: "internal_reference", label: "Internal Reference", type: "text", total: false },
    { key: "product_name", label: "Product Name", type: "text", total: false },
    { key: "brand", label: "Brand", type: "text", total: false },
    { key: "uom", label: "UOM", type: "text", total: false },
    { key: "current_qty", label: "Total Closing Qty", type: "number", total: true },
    { key: "current_value", label: "Total Closing Value", type: "amount", total: true },
    { key: "closing_avg_cost", label: "Closing Avg. Cost", type: "amount", total: false },
    { key: "qty_0_30", label: "Period 1 Qty", type: "number", total: true, bucketIndex: 0, bucketType: "Qty" },
    { key: "value_0_30", label: "Period 1 Value", type: "amount", total: true, bucketIndex: 0, bucketType: "Value" },
    { key: "qty_31_60", label: "Period 2 Qty", type: "number", total: true, bucketIndex: 1, bucketType: "Qty" },
    { key: "value_31_60", label: "Period 2 Value", type: "amount", total: true, bucketIndex: 1, bucketType: "Value" },
    { key: "qty_61_90", label: "Period 3 Qty", type: "number", total: true, bucketIndex: 2, bucketType: "Qty" },
    { key: "value_61_90", label: "Period 3 Value", type: "amount", total: true, bucketIndex: 2, bucketType: "Value" },
    { key: "qty_91_180", label: "Period 4 Qty", type: "number", total: true, bucketIndex: 3, bucketType: "Qty" },
    { key: "value_91_180", label: "Period 4 Value", type: "amount", total: true, bucketIndex: 3, bucketType: "Value" },
    { key: "qty_181_365", label: "Period 5 Qty", type: "number", total: true, bucketIndex: 4, bucketType: "Qty" },
    { key: "value_181_365", label: "Period 5 Value", type: "amount", total: true, bucketIndex: 4, bucketType: "Value" },
    { key: "qty_over_365", label: "Period 6 Qty", type: "number", total: true, bucketIndex: 5, bucketType: "Qty" },
    { key: "value_over_365", label: "Period 6 Value", type: "amount", total: true, bucketIndex: 5, bucketType: "Value" },
    { key: "oldest_stock_date", label: "Oldest Stock Date", type: "text", total: false },
    { key: "weighted_avg_age", label: "Weighted Avg. Age (Days)", type: "number", total: false },
    { key: "aged_qty_180", label: "Aged Qty", type: "number", total: true, dynamicType: "aged_qty" },
    { key: "aged_value_180", label: "Aged Value", type: "amount", total: true, dynamicType: "aged_value" },
    { key: "aged_percent_qty", label: "Aged % Qty", type: "percent", total: false },
    { key: "aged_percent_value", label: "Aged % Value", type: "percent", total: false },
    { key: "warehouse_qty_check", label: "Warehouse Qty Check", type: "number", total: true },
    { key: "warehouse_value_check", label: "Warehouse Value Check", type: "amount", total: true },
    { key: "no_movement_365", label: "No Movement", type: "flag", total: false, dynamicType: "no_movement" },
    { key: "aging_risk_level", label: "Risk Level", type: "risk", total: false },
    { key: "opening_inventory_value", label: "Opening Inventory Value", type: "amount", total: true },
    { key: "cogs_selected_period", label: "COGS - Selected Period", type: "amount", total: true },
    { key: "average_inventory_value", label: "Average Inventory Value", type: "amount", total: true },
    { key: "inventory_turnover_ratio", label: "Inventory Turnover Ratio", type: "number", total: true },
    { key: "dio_days", label: "DIO (Days)", type: "number", total: true },
];

const RISK_LEVELS = [
    { value: "LOW", label: "LOW" },
    { value: "MEDIUM", label: "MEDIUM" },
    { value: "HIGH", label: "HIGH" },
    { value: "CRITICAL", label: "CRITICAL" },
];

export class InventoryAgingDashboard extends Component {
    static template = "inventory_customs.InventoryAgingDashboard";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.riskOptions = RISK_LEVELS;
        this.dateInput = useRef("agingDateInput");

        this.filterSearchTimers = {
            warehouse: null,
            brand: null,
            category: null,
            product: null,
        };

        this.state = useState({
            rows: [],
            summary: {},
            columnTotals: {},
            isLoading: true,
            initialLoading: true,
            agingDate: "",
            agingPeriodDays: "30",
            viewMode: "detailed",
            page: 1,
            pageSize: 100,
            totalRows: 0,
            totalPages: 1,
            searchText: "",
            warehouseIds: [],
            brandValues: [],
            categoryIds: [],
            productIds: [],
            riskLevels: [],
            negativeStock: "all",
            noMovement: "all",
            detailedVisibleColumns: DETAILED_COLUMNS.map((column) => column.key),
            summaryVisibleColumns: SUMMARY_COLUMNS.map((column) => column.key),
            warehouseOptions: [],
            brandOptions: [],
            categoryOptions: [],
            productOptions: [],
            warehouseSearch: "",
            brandSearch: "",
            categorySearch: "",
            productSearch: "",
            warehouseOptionsLoaded: false,
            brandOptionsLoaded: false,
            categoryOptionsLoaded: false,
            productOptionsLoaded: false,
            showWarehouseDropdown: false,
            showBrandDropdown: false,
            showCategoryDropdown: false,
            showProductDropdown: false,
            showRiskDropdown: false,
            showColumnsDropdown: false,
        });

        this.onDocumentClick = this.onDocumentClick.bind(this);

        onMounted(async () => {
            document.addEventListener("click", this.onDocumentClick);
            this.state.isLoading = true;
            this.state.initialLoading = true;
            await this.waitForPaint();

            try {
                await this.loadDashboard();
            } catch (error) {
                console.error("Inventory Aging Initial Load Error:", error);
                this.notification.add("Unable to load Inventory Aging Dashboard.", { type: "danger" });
            } finally {
                this.state.initialLoading = false;
                this.state.isLoading = false;
            }
        });

        onWillUnmount(() => {
            document.removeEventListener("click", this.onDocumentClick);

            Object.values(this.filterSearchTimers).forEach((timer) => {
                if (timer) {
                    clearTimeout(timer);
                }
            });
        });
    }

    get availableColumns() {
        return this.state.viewMode === "summary" ? SUMMARY_COLUMNS : DETAILED_COLUMNS;
    }

    get selectedColumnKeys() {
        return this.state.viewMode === "summary"
            ? this.state.summaryVisibleColumns
            : this.state.detailedVisibleColumns;
    }

    get visibleColumns() {
        return this.availableColumns.filter((column) =>
            this.selectedColumnKeys.includes(column.key)
        );
    }

    get tableTitle() {
        return this.state.viewMode === "summary"
            ? "Product Inventory Aging Summary"
            : "Inventory Aging Details";
    }

    get riskLabel() {
        if (!this.state.riskLevels.length) {
            return "All Levels";
        }

        if (this.state.riskLevels.length === 1) {
            return this.state.riskLevels[0];
        }

        return `${this.state.riskLevels.length} Selected`;
    }

    getPeriodDays() {
        const value = String(
            this.state.agingPeriodDays || ""
        ).replace(/\D/g, "");

        const days = parseInt(
            value,
            10
        );

        return Number.isInteger(days) && days > 0
            ? days
            : 30;
    }

    getLastPeriodDays() {
        return this.getPeriodDays() * 5;
    }

    getAgedThresholdDays() {
        return Math.floor(
            this.getLastPeriodDays() / 2
        );
    }

    getPeriodLabel(index) {
        const days = this.getPeriodDays();

        if (index === 0) {
            return `0-${days}`;
        }

        if (index === 5) {
            return `>${days * 5}`;
        }

        return `${index * days + 1}-${(index + 1) * days}`;
    }

    getColumnLabel(column) {
        if (column.bucketIndex !== undefined) {
            return `${this.getPeriodLabel(column.bucketIndex)} ${column.bucketType}`;
        }

        if (column.dynamicType === "aged_qty") {
            return `Aged Qty >${this.getAgedThresholdDays()}`;
        }

        if (column.dynamicType === "aged_value") {
            return `Aged Value >${this.getAgedThresholdDays()}`;
        }

        if (column.dynamicType === "aged_percent_qty") {
            return `Aged >${this.getAgedThresholdDays()} % Qty`;
        }

        if (column.dynamicType === "aged_percent_value") {
            return `Aged >${this.getAgedThresholdDays()} % Value`;
        }

        if (column.dynamicType === "no_movement") {
            return `No Movement >${this.getLastPeriodDays()}`;
        }

        return column.label;
    }

    async waitForPaint() {
        await new Promise((resolve) => {
            requestAnimationFrame(() =>
                requestAnimationFrame(resolve)
            );
        });
    }

    onDocumentClick(ev) {
        const target = ev.target;

        if (!(target instanceof Element)) {
            return;
        }

        if (
            target.closest(".o_inv_dropdown_filter")
            ||
            target.closest(".o_inv_columns_area")
        ) {
            return;
        }

        this.closeAllDropdowns();
    }

    closeAllDropdowns() {
        this.state.showWarehouseDropdown = false;
        this.state.showBrandDropdown = false;
        this.state.showCategoryDropdown = false;
        this.state.showProductDropdown = false;
        this.state.showRiskDropdown = false;
        this.state.showColumnsDropdown = false;
    }

    openDatePicker(ev) {
        const input =
            this.dateInput.el
            ||
            ev.currentTarget;

        if (
            input
            &&
            typeof input.showPicker === "function"
        ) {
            try {
                input.showPicker();
            } catch (error) {
                console.debug(
                    "Unable to open date picker.",
                    error
                );
            }
        }
    }

    buildFilters() {
        return {
            aging_date:
                this.state.agingDate
                || false,

            aging_period_days:
                this.getPeriodDays(),

            view_mode:
                this.state.viewMode,

            warehouse_ids:
                this.state.warehouseIds,

            brand_values:
                this.state.brandValues,

            category_ids:
                this.state.categoryIds,

            product_ids:
                this.state.productIds,

            risk_levels:
                this.state.riskLevels,

            negative_stock:
                this.state.negativeStock,

            no_movement:
                this.state.noMovement,

            search_text:
                this.state.searchText,

            page:
                this.state.page,

            page_size:
                this.state.pageSize,
        };
    }

    async loadDashboard() {
        this.state.isLoading = true;

        await this.waitForPaint();

        try {
            const result = await this.orm.call(
                "inventory.aging.dashboard",
                "get_dashboard_data",
                [
                    this.buildFilters(),
                ]
            );

            this.state.rows =
                result.rows
                || [];

            this.state.summary =
                result.summary
                || {};

            this.state.columnTotals =
                result.column_totals
                || {};

            this.state.agingDate =
                result.aging_date
                ||
                this.state.agingDate
                ||
                "";

            this.state.agingPeriodDays =
                String(
                    result.aging_period_days
                    ||
                    this.getPeriodDays()
                );

            this.state.viewMode =
                result.view_mode
                ||
                this.state.viewMode
                ||
                "detailed";

            this.state.page =
                result.page
                || 1;

            this.state.pageSize =
                result.page_size
                || 100;

            this.state.totalRows =
                result.total_rows
                || 0;

            this.state.totalPages =
                result.total_pages
                || 1;

        } catch (error) {
            console.error(
                "Inventory Aging Dashboard Error:",
                error
            );

            this.notification.add(
                "Unable to load Inventory Aging Dashboard.",
                {
                    type: "danger",
                }
            );

        } finally {
            if (!this.state.initialLoading) {
                this.state.isLoading = false;
            }
        }
    }

    async selectViewMode(mode) {
        if (
            !["detailed", "summary"].includes(mode)
            ||
            this.state.viewMode === mode
        ) {
            return;
        }

        this.state.viewMode = mode;
        this.state.page = 1;

        this.closeAllDropdowns();

        await this.loadDashboard();
    }

    async loadWarehouseOptions(searchTerm = "") {
        this.state.warehouseOptions =
            await this.orm.call(
                "inventory.aging.dashboard",
                "search_filter_options",
                [
                    "warehouse",
                    searchTerm,
                    this.state.warehouseIds,
                ]
            );

        this.state.warehouseOptionsLoaded = true;
    }

    async loadBrandOptions(searchTerm = "") {
        this.state.brandOptions =
            await this.orm.call(
                "inventory.aging.dashboard",
                "search_filter_options",
                [
                    "brand",
                    searchTerm,
                    this.state.brandValues,
                ]
            );

        this.state.brandOptionsLoaded = true;
    }

    async loadCategoryOptions(searchTerm = "") {
        this.state.categoryOptions =
            await this.orm.call(
                "inventory.aging.dashboard",
                "search_filter_options",
                [
                    "category",
                    searchTerm,
                    this.state.categoryIds,
                ]
            );

        this.state.categoryOptionsLoaded = true;
    }

    async loadProductOptions(searchTerm = "") {
        this.state.productOptions =
            await this.orm.call(
                "inventory.aging.dashboard",
                "search_filter_options",
                [
                    "product",
                    searchTerm,
                    this.state.productIds,
                ]
            );

        this.state.productOptionsLoaded = true;
    }

    async toggleWarehouseDropdown() {
        const opening =
            !this.state.showWarehouseDropdown;

        this.closeAllDropdowns();

        this.state.showWarehouseDropdown =
            opening;

        if (
            opening
            &&
            !this.state.warehouseOptionsLoaded
        ) {
            await this.loadWarehouseOptions();
        }
    }

    async toggleBrandDropdown() {
        const opening =
            !this.state.showBrandDropdown;

        this.closeAllDropdowns();

        this.state.showBrandDropdown =
            opening;

        if (
            opening
            &&
            !this.state.brandOptionsLoaded
        ) {
            await this.loadBrandOptions();
        }
    }

    async toggleCategoryDropdown() {
        const opening =
            !this.state.showCategoryDropdown;

        this.closeAllDropdowns();

        this.state.showCategoryDropdown =
            opening;

        if (
            opening
            &&
            !this.state.categoryOptionsLoaded
        ) {
            await this.loadCategoryOptions();
        }
    }

    async toggleProductDropdown() {
        const opening =
            !this.state.showProductDropdown;

        this.closeAllDropdowns();

        this.state.showProductDropdown =
            opening;

        if (
            opening
            &&
            !this.state.productOptionsLoaded
        ) {
            await this.loadProductOptions();
        }
    }

    toggleRiskDropdown() {
        const opening =
            !this.state.showRiskDropdown;

        this.closeAllDropdowns();

        this.state.showRiskDropdown =
            opening;
    }

    toggleColumnsDropdown() {
        const opening =
            !this.state.showColumnsDropdown;

        this.closeAllDropdowns();

        this.state.showColumnsDropdown =
            opening;
    }

    scheduleFilterSearch(
        filterName,
        value
    ) {
        if (
            this.filterSearchTimers[
                filterName
            ]
        ) {
            clearTimeout(
                this.filterSearchTimers[
                    filterName
                ]
            );
        }

        this.filterSearchTimers[
            filterName
        ] = setTimeout(
            async () => {
                if (
                    filterName
                    === "warehouse"
                ) {
                    await this.loadWarehouseOptions(
                        value
                    );

                } else if (
                    filterName
                    === "brand"
                ) {
                    await this.loadBrandOptions(
                        value
                    );

                } else if (
                    filterName
                    === "category"
                ) {
                    await this.loadCategoryOptions(
                        value
                    );

                } else if (
                    filterName
                    === "product"
                ) {
                    await this.loadProductOptions(
                        value
                    );
                }
            },
            300
        );
    }

    onWarehouseSearch(ev) {
        this.state.warehouseSearch =
            ev.target.value;

        this.scheduleFilterSearch(
            "warehouse",
            this.state.warehouseSearch
        );
    }

    onBrandSearch(ev) {
        this.state.brandSearch =
            ev.target.value;

        this.scheduleFilterSearch(
            "brand",
            this.state.brandSearch
        );
    }

    onCategorySearch(ev) {
        this.state.categorySearch =
            ev.target.value;

        this.scheduleFilterSearch(
            "category",
            this.state.categorySearch
        );
    }

    onProductSearch(ev) {
        this.state.productSearch =
            ev.target.value;

        this.scheduleFilterSearch(
            "product",
            this.state.productSearch
        );
    }

    async onAgingDateChange(ev) {
        this.state.agingDate =
            ev.target.value;

        this.state.page =
            1;

        this.closeAllDropdowns();

        await this.loadDashboard();
    }

    onAgingPeriodDaysInput(ev) {
        let value =
            ev.target.value.replace(
                /\D/g,
                ""
            );

        value =
            value.replace(
                /^0+(?=\d)/,
                ""
            );

        this.state.agingPeriodDays =
            value;

        ev.target.value =
            value;
    }

    async onAgingPeriodDaysChange(ev) {
        let value =
            String(
                ev.target.value
                || ""
            ).replace(
                /\D/g,
                ""
            );

        value =
            value.replace(
                /^0+(?=\d)/,
                ""
            );

        let days =
            parseInt(
                value,
                10
            );

        if (
            !Number.isInteger(days)
            ||
            days < 1
        ) {
            days =
                30;
        }

        this.state.agingPeriodDays =
            String(
                days
            );

        ev.target.value =
            String(
                days
            );

        this.state.page =
            1;

        this.closeAllDropdowns();

        await this.loadDashboard();
    }

    async onSearchChange(ev) {
        this.state.searchText =
            ev.target.value;

        this.state.page =
            1;

        this.closeAllDropdowns();

        await this.loadDashboard();
    }

    async onNegativeStockChange(ev) {
        this.state.negativeStock =
            ev.target.value;

        this.state.page =
            1;

        this.closeAllDropdowns();

        await this.loadDashboard();
    }

    async onNoMovementChange(ev) {
        this.state.noMovement =
            ev.target.value;

        this.state.page =
            1;

        this.closeAllDropdowns();

        await this.loadDashboard();
    }

    async toggleWarehouse(value) {
        const id =
            Number(
                value
            );

        this.state.warehouseIds =
            this.state.warehouseIds.includes(
                id
            )
                ?
                this.state.warehouseIds.filter(
                    (item) =>
                        item !== id
                )
                :
                [
                    ...this.state.warehouseIds,
                    id,
                ];

        this.state.page =
            1;

        await this.loadDashboard();
    }

    async toggleBrand(value) {
        const id =
            Number(
                value
            );

        this.state.brandValues =
            this.state.brandValues.includes(
                id
            )
                ?
                this.state.brandValues.filter(
                    (item) =>
                        item !== id
                )
                :
                [
                    ...this.state.brandValues,
                    id,
                ];

        this.state.page =
            1;

        await this.loadDashboard();
    }

    async toggleCategory(value) {
        const id =
            Number(
                value
            );

        this.state.categoryIds =
            this.state.categoryIds.includes(
                id
            )
                ?
                this.state.categoryIds.filter(
                    (item) =>
                        item !== id
                )
                :
                [
                    ...this.state.categoryIds,
                    id,
                ];

        this.state.page =
            1;

        await this.loadDashboard();
    }

    async toggleProduct(value) {
        const id =
            Number(
                value
            );

        this.state.productIds =
            this.state.productIds.includes(
                id
            )
                ?
                this.state.productIds.filter(
                    (item) =>
                        item !== id
                )
                :
                [
                    ...this.state.productIds,
                    id,
                ];

        this.state.page =
            1;

        await this.loadDashboard();
    }

    async toggleRisk(value) {
        this.state.riskLevels =
            this.state.riskLevels.includes(
                value
            )
                ?
                this.state.riskLevels.filter(
                    (level) =>
                        level !== value
                )
                :
                [
                    ...this.state.riskLevels,
                    value,
                ];

        this.state.page =
            1;

        await this.loadDashboard();
    }

    isRiskSelected(value) {
        return this.state.riskLevels.includes(
            value
        );
    }

    toggleColumn(columnKey) {
        if (
            this.state.viewMode
            === "summary"
        ) {
            this.state.summaryVisibleColumns =
                this.state.summaryVisibleColumns.includes(
                    columnKey
                )
                    ?
                    this.state.summaryVisibleColumns.filter(
                        (key) =>
                            key !== columnKey
                    )
                    :
                    [
                        ...this.state.summaryVisibleColumns,
                        columnKey,
                    ];

        } else {
            this.state.detailedVisibleColumns =
                this.state.detailedVisibleColumns.includes(
                    columnKey
                )
                    ?
                    this.state.detailedVisibleColumns.filter(
                        (key) =>
                            key !== columnKey
                    )
                    :
                    [
                        ...this.state.detailedVisibleColumns,
                        columnKey,
                    ];
        }
    }

    selectAllColumns() {
        if (
            this.state.viewMode
            === "summary"
        ) {
            this.state.summaryVisibleColumns =
                SUMMARY_COLUMNS.map(
                    (column) =>
                        column.key
                );

        } else {
            this.state.detailedVisibleColumns =
                DETAILED_COLUMNS.map(
                    (column) =>
                        column.key
                );
        }
    }

    isColumnSelected(columnKey) {
        return this.selectedColumnKeys.includes(
            columnKey
        );
    }

    async clearFilters() {
        this.state.warehouseIds = [];
        this.state.brandValues = [];
        this.state.categoryIds = [];
        this.state.productIds = [];
        this.state.riskLevels = [];

        this.state.negativeStock =
            "all";

        this.state.noMovement =
            "all";

        this.state.searchText =
            "";

        this.state.agingPeriodDays =
            "30";

        this.state.page =
            1;

        this.state.warehouseSearch =
            "";

        this.state.brandSearch =
            "";

        this.state.categorySearch =
            "";

        this.state.productSearch =
            "";

        this.state.warehouseOptions =
            [];

        this.state.brandOptions =
            [];

        this.state.categoryOptions =
            [];

        this.state.productOptions =
            [];

        this.state.warehouseOptionsLoaded =
            false;

        this.state.brandOptionsLoaded =
            false;

        this.state.categoryOptionsLoaded =
            false;

        this.state.productOptionsLoaded =
            false;

        this.closeAllDropdowns();

        await this.loadDashboard();
    }

    async previousPage() {
        if (
            this.state.page
            <= 1
        ) {
            return;
        }

        this.state.page -=
            1;

        this.closeAllDropdowns();

        await this.loadDashboard();
    }

    async nextPage() {
        if (
            this.state.page
            >=
            this.state.totalPages
        ) {
            return;
        }

        this.state.page +=
            1;

        this.closeAllDropdowns();

        await this.loadDashboard();
    }

    async exportExcel() {
        this.state.isLoading =
            true;

        this.closeAllDropdowns();

        await this.waitForPaint();

        try {
            const action =
                await this.orm.call(
                    "inventory.aging.dashboard",
                    "export_excel",
                    [
                        this.buildFilters(),
                    ]
                );

            if (
                action
                &&
                action.url
            ) {
                window.location.href =
                    action.url;
            }

        } catch (error) {
            console.error(
                "Inventory Aging Export Error:",
                error
            );

            this.notification.add(
                "Unable to export Inventory Aging.",
                {
                    type: "danger",
                }
            );

        } finally {
            this.state.isLoading =
                false;
        }
    }

    formatNumber(value) {
        return Number(
            value
            || 0
        ).toLocaleString(
            undefined,
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            }
        );
    }

    formatPercent(value) {
        return `${
            (
                Number(
                    value
                    || 0
                )
                * 100
            ).toLocaleString(
                undefined,
                {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                }
            )
        }%`;
    }

    formatCell(
        row,
        column
    ) {
        const value =
            row[
                column.key
            ];

        if (
            value === null
            ||
            value === undefined
            ||
            value === false
        ) {
            return "";
        }

        if (
            column.type
            === "number"
            ||
            column.type
            === "amount"
        ) {
            return this.formatNumber(
                value
            );
        }

        if (
            column.type
            === "percent"
        ) {
            return this.formatPercent(
                value
            );
        }

        return value;
    }

    getColumnClass(column) {
        return (
            column.key
            === "product_name"
                ?
                "o_inv_product_column"
                :
                "o_inv_center_column"
        );
    }

    getTotalValue(column) {
        if (
            !column.total
        ) {
            return "";
        }

        return this.formatNumber(
            this.state.columnTotals[
                column.key
            ]
            || 0
        );
    }

    isWarehouseSelected(value) {
        return this.state.warehouseIds.includes(
            Number(
                value
            )
        );
    }

    isBrandSelected(value) {
        return this.state.brandValues.includes(
            Number(
                value
            )
        );
    }

    isCategorySelected(value) {
        return this.state.categoryIds.includes(
            Number(
                value
            )
        );
    }

    isProductSelected(value) {
        return this.state.productIds.includes(
            Number(
                value
            )
        );
    }

    get warehouseLabel() {
        return (
            this.state.warehouseIds.length
                ?
                `${this.state.warehouseIds.length} Selected`
                :
                "All Warehouses"
        );
    }

    get brandLabel() {
        return (
            this.state.brandValues.length
                ?
                `${this.state.brandValues.length} Selected`
                :
                "All Brands"
        );
    }

    get categoryLabel() {
        return (
            this.state.categoryIds.length
                ?
                `${this.state.categoryIds.length} Selected`
                :
                "All Categories"
        );
    }

    get productLabel() {
        return (
            this.state.productIds.length
                ?
                `${this.state.productIds.length} Selected`
                :
                "All Products"
        );
    }
}

registry.category("actions").add(
    "inventory_aging_dashboard",
    InventoryAgingDashboard
);