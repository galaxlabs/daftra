app_name = "daftra"
app_title = "Daftra"
app_publisher = "Galaxy Labs"
app_description = "Complete ERP System - Daftra Clone"
app_icon = "octicon octicon-file-directory"
app_color = "#589494"
app_email = "galaxylab2020@gmail.com"
app_license = "MIT"
required_apps = []
source_url = "https://galaxylab2020.daftra.com"

# Apps
app_include_js = []
app_include_css = []
web_include_js = []
web_include_css = []

# Fixtures
fixtures = []

# Permissions
permissions = [
    {
        "role": "System Manager",
        "doctypes": [
            "Daftra Settings", "Tax Setting", "Account", "Cost Center",
            "Treasury", "Bank Registration", "Employee Role", "Shift", "Daftra Project"
        ]
    },
    {
        "role": "Accounts Manager",
        "doctypes": [
            "Sales Invoice", "Purchase Invoice", "Journal Entry",
            "Invoice Payment", "Supplier Payment", "Expense", "Income", "Bank Registration"
        ]
    },
    {
        "role": "Sales Manager",
        "doctypes": [
            "Sales Invoice", "Sales Quotation", "Client",
            "Invoice Payment", "Product"
        ]
    },
    {
        "role": "HR Manager",
        "doctypes": [
            "Employee", "Employee Attendance", "Payroll Entry",
            "Leave Request", "Employee Contract"
        ]
    },
    {
        "role": "Purchase Manager",
        "doctypes": [
            "Purchase Order", "Purchase Invoice", "Supplier",
            "Purchase Request", "Purchase Quotation"
        ]
    },
    {
        "role": "Stock Manager",
        "doctypes": [
            "Product", "Warehouse", "Stock Entry", "Stocktaking", "Daftra Project"
        ]
    },
]



override_doctype_class = {
    "Daftra Project": "daftra.daftra_projects.doctype.daftra_project.daftra_project.DaftraProject",
}

doctype_js = {
    "Sales Invoice": "public/js/daftra_forms.js",
    "Sales Quotation": "public/js/daftra_forms.js",
    "Purchase Invoice": "public/js/daftra_forms.js",
    "Time Entry": "public/js/daftra_forms.js",
    "Daftra Settings": "public/js/daftra_forms.js",
    "Invoice Payment": "public/js/daftra_forms.js",
    "Supplier Payment": "public/js/daftra_forms.js",
}


doc_events = {
    "Daftra Project": {
        "on_update": "daftra.api.project_api.refresh_project_document",
    },
    "Sales Invoice": {
        "after_insert": "daftra.api.project_api.refresh_project_from_doc",
        "on_submit": "daftra.api.project_api.refresh_project_from_doc",
        "on_update_after_submit": "daftra.api.project_api.refresh_project_from_doc",
    },
    "Purchase Invoice": {
        "after_insert": "daftra.api.project_api.refresh_project_from_doc",
        "on_submit": "daftra.api.project_api.refresh_project_from_doc",
        "on_update_after_submit": "daftra.api.project_api.refresh_project_from_doc",
    },
    "Expense": {
        "after_insert": "daftra.api.project_api.refresh_project_from_doc",
        "on_update": "daftra.api.project_api.refresh_project_from_doc",
    },
    "Income": {
        "after_insert": "daftra.api.project_api.refresh_project_from_doc",
        "on_update": "daftra.api.project_api.refresh_project_from_doc",
    },
    "Journal Entry": {
        "after_insert": "daftra.api.project_api.refresh_project_from_doc",
        "on_submit": "daftra.api.project_api.refresh_project_from_doc",
        "on_update_after_submit": "daftra.api.project_api.refresh_project_from_doc",
    },
    "Time Entry": {
        "after_insert": "daftra.api.project_api.refresh_project_from_doc",
        "on_update": "daftra.api.project_api.refresh_project_from_doc",
    },
    "Booking": {
        "after_insert": "daftra.api.project_api.refresh_project_from_doc",
        "on_update": "daftra.api.project_api.refresh_project_from_doc",
    },
}
