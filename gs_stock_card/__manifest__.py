{
	"name": "GS Stock Card",
	"depends": [
		"base",
		"stock",
	], 
	"author": "Global Solutions",
	"company": "Global Solutions",
	"maintainer": "Global Solutions",
	"website": "https://globalsolutions.dev",
	"category": "Warehouse",
	'summary': """Print (Stock Card) PDF/XLSX Report of Products/Product Variants
with Lots/Serial Number and Expired Date.""",
	"description": """
Features:
* Print (Stock Card) of some Product / Product Variants on spesific Warehouse location
* Show Specific Date Range or Last Day number
* Output Report in PDF or Excel (XLSX) file format
* Display Lots/Serial Number and Expired Date

  This Report has some columns:
    - Date 
    - In
    - Out
    - Stock
    - Batch # (Lot)
    - ED  (Expired Date)
    - Distributor (Seller)
    - Buyer
""",
	"data": [
	'security/ir.model.access.csv',
	"report/product_product.xml",
	"wizard/kartu_stok_report.xml"
	],
	'images': ['static/description/images/main_report.gif'],
	"application": True,
	"installable": True,
	"auto_install": False,
	"license": "AGPL-3",
}

