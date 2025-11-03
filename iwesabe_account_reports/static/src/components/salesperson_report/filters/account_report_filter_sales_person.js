/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Component, useState } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { MultiRecordSelector } from "@web/core/record_selectors/multi_record_selector";

/**
 * SalesPerson filter component for account reports
 * This component shows a dropdown with SalesPerson filter specifically for Partner Ledger
 */
export class AccountReportFilterSalesPerson extends Component {
    static template = "iwesabe_account_reports.AccountReportFilterSalesPerson";
    static components = { Dropdown, MultiRecordSelector };
    static props = {
        report: Object,
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            selectedSalesPerson: this._getSelectedSalesPersonName(),
        });
    }

    /**
     * Get the name of the currently selected sales person for display
     */
    _getSelectedSalesPersonName() {
        const selectedIds = this.props.report.options.salespersons || [];
        if (selectedIds.length === 1) {
            // If we have selected records, try to get the name from the recordList (if loaded)
            const recordList = this.props.report.searchModel?.recordLists?.['res.users'] || [];
            const record = recordList.find(r => r.id === selectedIds[0]);
            if (record) {
                return record.display_name;
            }
            return `Sales Person (${selectedIds.length})`;
        } else if (selectedIds.length > 1) {
            return `Sales Person (${selectedIds.length})`;
        }
        return "Sales Person";
    }

    /**
     * Returns props for the MultiRecordSelector component
     */
    getMultiRecordSelectorProps() {
        return {
            resModel: "res.users",
            domain: [['share', '=', false]], // Only internal users
            value: this.props.report.options.salespersons || [],
            update: (value) => this.onFilterValueChanged(value),
            searchPlaceholder: _t("Search..."),
        };
    }

    /**
     * Handles value changes in the filter
     */
    async onFilterValueChanged(value) {
        this.props.report.options.salespersons = value;

        // Update displayed name
        this.state.selectedSalesPerson = this._getSelectedSalesPersonName();

        // Reload the report
        await this.props.report.reload();
    }
}

// Register the filter component factory
registry.category("account_report_filter").add("sales_person", {
    title: _t("Sales Person"),
    component: AccountReportFilterSalesPerson,
    // Condition to show this filter
    shouldDisplay: (env) => {
        return env.report.options.salesperson;
    },
});

// Patch the main account report model to ensure 'salesperson' option is available
const accountReportModelPatch = {
    /**
     * @override
     */
    _getDefaultOptions(options) {
        const defaultOptions = this._super(...arguments);
        // Add salesperson option
        if (defaultOptions.report_type === 'partner_ledger') { // Show it for Partner Ledger report
            defaultOptions.salesperson = true;
        }
        return defaultOptions;
    },

    /**
     * @override
     */
    async _updateReportOptions(options) {
        await this._super(...arguments);
        // If the report should show salesperson filter, make sure we have the data
        if (options.salesperson && (!options.salespersons || options.salespersons.length === 0)) {
            // Preload sales users for the dropdown
            const orm = this.env.services.orm;
            const result = await orm.call("res.users", "search_read",
                [[['share', '=', false]]], // Domain for internal users
                ['id', 'name'],
                { limit: 80 }
            );

            // Create record list for the selector
            const recordList = result.map(r => ({
                id: r.id,
                display_name: r.name,
            }));

            if (!this.recordLists) {
                this.recordLists = {};
            }
            this.recordLists['res.users'] = recordList;
        }
    },
};

// Register the model patch
registry.category("account_report_model_patch").add("iwesabe_sales_person", accountReportModelPatch);