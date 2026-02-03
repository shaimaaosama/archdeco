/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { loadJS, loadCSS } from "@web/core/assets";
import { useService } from "@web/core/utils/hooks";
import { useModelWithSampleData } from "@web/model/model";
import { standardViewProps } from "@web/views/standard_view_props";
import { useSetupView } from "@web/views/view_hook";
import { Layout } from "@web/search/layout";
import { session } from "@web/session";
import { SearchBar } from "@web/search/search_bar/search_bar";
import { useSearchBarToggler } from "@web/search/search_bar/search_bar_toggler";
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
import {formatDateTime, deserializeDateTime, serializeDate } from "@web/core/l10n/dates";
import { Component, onWillUnmount, onWillStart, useRef, useState } from "@odoo/owl";

const { DateTime } = luxon;

export class GeofenceController extends Component {
    setup() {
        const Model = this.props.Model;
        const model = useModelWithSampleData(Model, this.props.modelParams);
        this.model = model;

        useSetupView({
            getLocalState: () => {
                return this.model.metaData;
            },
        });

        onWillStart(async () => {
            await loadCSS("/pt_attendance_portal/static/src/js/lib/ol-6.12.0/ol.css");
            await loadCSS("/pt_attendance_portal/static/src/js/lib/ol-ext/ol-ext.css");
            await loadJS("/pt_attendance_portal/static/src/js/lib/ol-6.12.0/ol.js");
            await loadJS("/pt_attendance_portal/static/src/js/lib/ol-ext/ol-ext.js");
        });

        this.searchBarToggler = useSearchBarToggler();
    }

    get rendererProps() {
        return {
            model: this.model,
        };
    }
}

GeofenceController.template = "pt_attendance_portal.Contoller";
GeofenceController.components = {
    Layout,
    SearchBar,
};

GeofenceController.props = {
    ...standardViewProps,
    Model: Function,
    modelParams: Object,
    Renderer: Function,
    buttonTemplate: String,
};
