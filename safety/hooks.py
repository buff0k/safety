app_name = "safety"
app_title = "Safety"
app_publisher = "BuFf0k"
app_description = "Safety Incident Management System for Mining"
app_email = "buff0k@gmail.com"
app_license = "mit"
app_version = "16.0.0"
required_apps = ["frappe/hrms"]
source_link = "http://github.com/buff0k/safety"
app_logo_url = "/assets/safety/images/is-logo.svg"
app_home = "/desk/safety"
add_to_apps_screen = [
	{
		"name": app_name,
		"logo": "/assets/safety/images/is-logo.svg",
		"title": app_title,
		"route": app_home,
		"has_permission": "safety.safety.utils.check_app_permission",
	}
]
fixtures = [
	{"dt": "Role", "filters": [["name", "in", [
		"Safety Manager",
		"Safety User"
	]]]},
	{"dt": "Custom DocPerm", "filters": [["role", "in", [
		"Safety Manager",
		"Safety User"
	]]]},
	{"dt": "Safety Incident Classification", "filters": [["name", "in", [
		"Fatality",
		"Lost Time Injury",
		"Minor Injury",
		"Near Miss",
		"Unsafe Act"
	]]]}
]