frappe.pages['inventory-summary'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Inventory Summary',
		single_column: true
	});
}