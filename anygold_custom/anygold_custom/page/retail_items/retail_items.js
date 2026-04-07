frappe.pages['retail-items'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Retail Items',
		single_column: true
	});
}