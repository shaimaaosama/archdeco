{
    "name": "Project Status & UBR Dashboard",
    "version": "18.0.1.0.0",
    "category": "Project",
    "summary": "Interactive Project Status & UBR dashboard with Excel export Customizations",

    'description': """
    - Project Status & UBR.
    - Bill of Quantities.
    """,
    "author": "Hadeel Ali - ArchDeco",
    "license": "LGPL-3",
    "depends": [
        "project",
        "sale_management",
        "account",
        "web",
        "sh_secondary_unit",
        "gs_sale_quotation_report_custom",
        "gs_sales_permission",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security_view.xml",
        "views/project_project_views.xml",
        "views/project_status_ubr_menu.xml",
        "views/sale_order.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "project_status_ubr_dashboard/static/src/project_status_ubr/project_status_ubr.js",
            "project_status_ubr_dashboard/static/src/project_status_ubr/project_status_ubr.xml",
            "project_status_ubr_dashboard/static/src/project_status_ubr/project_status_ubr.scss",
        ],
    },
    "installable": True,
    "application": True,
}
