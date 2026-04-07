frappe.pages['stock-check-history'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Stock Check History',
		single_column: true
	});
}