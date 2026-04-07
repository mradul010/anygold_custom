frappe.pages['pending-actions'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Pending Actions',
		single_column: true
	});
}