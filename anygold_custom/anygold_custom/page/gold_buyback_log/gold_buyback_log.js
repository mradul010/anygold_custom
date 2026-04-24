const GOLD_BUYBACK_DOCTYPE = "Gold Buyback Submission";

function goToBuybackLogList() {
	frappe.set_route("List", GOLD_BUYBACK_DOCTYPE, "List");
}

frappe.pages["gold-buyback-log"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Gold Buyback Log",
		single_column: true,
	});

	page.set_primary_action(__("Open Gold Buyback Log"), () => {
		goToBuybackLogList();
	});

	$(wrapper).find(".layout-main-section").html(`
		<div style="padding: 16px;">
			<div style="font-size: 14px; margin-bottom: 8px;">
				This page redirects to the <strong>${GOLD_BUYBACK_DOCTYPE}</strong> list.
			</div>
			<div style="font-size: 12px; color: var(--text-muted);">
				Use this as your central log for all submitted gold buybacks.
			</div>
		</div>
	`);
};

frappe.pages["gold-buyback-log"].on_page_show = function () {
	goToBuybackLogList();
};
