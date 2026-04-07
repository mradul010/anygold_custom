frappe.pages['customer-list'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Customer List',
		single_column: true
	});
}