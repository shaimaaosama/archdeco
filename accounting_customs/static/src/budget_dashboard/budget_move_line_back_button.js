/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);
        this.budgetDashboardAction = useService("action");
    },

    get isBudgetDashboardMoveLineAction() {
        const context = this.props.context || {};

        return (
            this.props.resModel === "account.move.line" &&
            context.from_budget_dashboard
        );
    },

    async onBackToBudgetDashboard() {
        const context = this.props.context || {};

        await this.budgetDashboardAction.doAction({
            type: "ir.actions.client",
            tag: "account_budget_dashboard",
            name: "Budget Dashboard",
            params: {
                budget_id: context.budget_dashboard_budget_id,
                year: context.budget_dashboard_year,
                date_from: context.budget_dashboard_date_from,
                date_to: context.budget_dashboard_date_to,
                screen: "budget",
            },
        });
    },
});