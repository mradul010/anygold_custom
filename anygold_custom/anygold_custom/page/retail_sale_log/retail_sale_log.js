frappe.pages['retail-sale-log'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Retail Sale Log',
		single_column: true
	});
}