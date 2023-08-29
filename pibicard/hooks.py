from . import __version__ as app_version

app_name = "pibicard"
app_title = "pibiCARD"
app_publisher = "pibiCo"
app_description = "cardDAV Frappe App"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "pibico.sl@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/pibicard/css/pibicard.css"
# app_include_js = "/assets/pibicard/js/pibicard.js"

# include js, css files in header of web template
# web_include_css = "/assets/pibicard/css/pibicard.css"
# web_include_js = "/assets/pibicard/js/pibicard.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "pibicard/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
  "Contact": [
    "public/js/contact.js"
  ]
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
doctype_list_js = {
  "Contact": "public/js/contact_list.js"
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "pibicard.install.before_install"
# after_install = "pibicard.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "pibicard.uninstall.before_uninstall"
# after_uninstall = "pibicard.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "pibicard.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }
override_doctype_class = {
  "Contact": "pibicard.overrides.contact.CustomContact",
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
	"all": [
		#"pibicard.overrides.contact.schedule_synchronization",
    #"pibicard.overrides.contact.synchronize_carddav_contacts"
	],
#	"daily": [
#		"pibicard.tasks.daily"
#	],
#	"hourly": [
#		"pibicard.tasks.hourly"
#	],
#	"weekly": [
#		"pibicard.tasks.weekly"
#	]
#	"monthly": [
#		"pibicard.tasks.monthly"
#	]
 }

# Testing
# -------

# before_tests = "pibicard.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "pibicard.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "pibicard.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Request Events
# ----------------
# before_request = ["pibicard.utils.before_request"]
# after_request = ["pibicard.utils.after_request"]

# Job Events
# ----------
# before_job = ["pibicard.utils.before_job"]
# after_job = ["pibicard.utils.after_job"]

# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"pibicard.auth.validate"
# ]

fixtures = [
  {
    "dt": "Custom Field",
    "filters": [["dt", "in", ("Contact")], ["name", "like", "%cr_%"]]
  },
  {
    "dt": "Client Script",
    "filters": [["dt", "in", ("Contact")], ["name", "like", "%cr_%"]]
  },
  {
    "dt": "Property Setter",
    "filters": []
  },  
]