/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { GeofenceArchParser } from "./geofence_arch_parser";
import { GeofenceController } from "./geofence_controller";
import { GeofenceRenderer } from "./geofence_renderer";
import { GeofenceModel } from "./geofence_model";

export const GeofenceView = {
    type: "geofence_view",
    ArchParser: GeofenceArchParser,
    Controller: GeofenceController,
    Model: GeofenceModel,
    Renderer: GeofenceRenderer,
    searchMenuTypes: ["filter"],
    buttonTemplate: "pt_attendance_portal.Buttons",
    props: (genericProps, view) => {
        let modelParams = genericProps.state;
        if (!modelParams) {
            const { arch, relatedModels, resModel, fields, context} = genericProps;
            const parser = new view.ArchParser();
            const archInfo = parser.parse(arch, relatedModels, resModel);
            modelParams = {
                context: context,
                fields: fields,
                fieldNames: archInfo.fieldNames,
                overlayPaths: archInfo.overlay_paths || false,
                resModel: resModel,
                defaultOrder: 'id',
            };
        }

        return {
            ...genericProps,
            Model: view.Model,
            modelParams,
            Renderer: view.Renderer,
            buttonTemplate: view.buttonTemplate,
        };
    }
};

// Ensure the view type is in session.view_info for validation
if (session.view_info && !session.view_info.geofence_view) {
    session.view_info.geofence_view = {
        multi_record: true,
    };
}

registry.category('views').add('geofence_view', GeofenceView);
