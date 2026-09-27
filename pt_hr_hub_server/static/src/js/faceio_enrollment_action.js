/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

class FaceIOEnrollmentAction extends Component {
    static template = "pt_hr_hub_server.FaceIOEnrollmentAction";

    get enrollUrl() {
        const employeeId = this.props.action?.context?.employee_id || "";
        return `/hr_hub/faceio/enroll?employee_id=${employeeId}`;
    }
}

registry.category("actions").add("faceio_enrollment_action", FaceIOEnrollmentAction);
