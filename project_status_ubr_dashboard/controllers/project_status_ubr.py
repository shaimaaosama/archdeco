import json

from odoo import http
from odoo.http import content_disposition, request


class ProjectStatusUBRController(http.Controller):

    @http.route(
        "/project_status_ubr/export_xlsx",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def export_xlsx(self, filters="{}", **kwargs):
        try:
            parsed_filters = json.loads(filters or "{}")
        except (TypeError, ValueError):
            parsed_filters = {}

        content = request.env["project.status.ubr.dashboard"].get_excel_file(
            parsed_filters
        )
        filename = "Project_Status_UBR.xlsx"
        return request.make_response(
            content,
            headers=[
                ("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                ("Content-Disposition", content_disposition(filename)),
                ("Content-Length", len(content)),
            ],
        )
