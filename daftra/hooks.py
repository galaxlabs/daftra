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
app_include_css = ["/assets/daftra/css/daftra.css"]
web_include_js = []
web_include_css = ["/assets/daftra/css/daftra.css"]

# Fixtures
fixtures = ["Print Format", "Workspace", "Custom Field"]

# Permissions
permissions = [
    {
        "role": "System Manager",
        "doctypes": [
            "Daftra Settings", "Tax Setting", "Account", "Cost Center",
            "Treasury", "Employee Role", "Shift"
        ]
    },
    {
        "role": "Accounts Manager",
        "doctypes": [
            "Sales Invoice", "Purchase Invoice", "Journal Entry",
            "Invoice Payment", "Supplier Payment", "Expense", "Income"
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
            "Product", "Warehouse", "Stock Entry", "Stocktaking"
        ]
    },
]


doctype_js = {
    "Sales Invoice": "public/js/daftra_forms.js",
    "Sales Quotation": "public/js/daftra_forms.js",
    "Purchase Invoice": "public/js/daftra_forms.js",
    "Time Entry": "public/js/daftra_forms.js",
    "Daftra Settings": "public/js/daftra_forms.js",
}
