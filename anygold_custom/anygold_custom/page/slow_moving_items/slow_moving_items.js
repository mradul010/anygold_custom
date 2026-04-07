frappe.pages['slow-moving-items'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Slow Moving Items',
		single_column: true
	});
}