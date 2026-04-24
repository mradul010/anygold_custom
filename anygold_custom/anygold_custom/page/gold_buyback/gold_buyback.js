frappe.pages["gold-buyback"].on_page_load = function (wrapper) {
	attach_route_style_guard();
	ensure_gold_buyback_styles();

	frappe.ui.make_app_page({
		parent: wrapper,
		title: "Gold Buyback",
		single_column: true,
	});
};

frappe.pages["gold-buyback"].on_page_show = async function (wrapper) {
	ensure_gold_buyback_styles();
	await load_vue(wrapper);
};

const GOLD_BUYBACK_STYLE_ID = "anygold-gold-buyback-css";
const GOLD_BUYBACK_STYLE_HREF = "/assets/anygold_custom/css/main.css";
const GOLD_BUYBACK_BUNDLE_PATHS = [
	"/assets/anygold_custom/js/gold_buyback.bundle.js",
	"gold_buyback.bundle.js",
];
let has_route_style_guard = false;
let gold_buyback_load_seq = 0;

function ensure_gold_buyback_styles() {
	if (document.getElementById(GOLD_BUYBACK_STYLE_ID)) return;

	const link = document.createElement("link");
	link.id = GOLD_BUYBACK_STYLE_ID;
	link.rel = "stylesheet";
	link.href = GOLD_BUYBACK_STYLE_HREF;
	document.head.appendChild(link);
}

function remove_gold_buyback_styles() {
	const link = document.getElementById(GOLD_BUYBACK_STYLE_ID);
	if (link) link.remove();
}

function is_gold_buyback_route() {
	const route = frappe.get_route?.();
	return Array.isArray(route) && route[0] === "gold-buyback";
}

function attach_route_style_guard() {
	if (has_route_style_guard || !frappe.router || typeof frappe.router.on !== "function") return;

	frappe.router.on("change", () => {
		if (is_gold_buyback_route()) {
			ensure_gold_buyback_styles();
			return;
		}

		unmount_stale_gold_buyback_app();
		remove_gold_buyback_styles();
	});

	has_route_style_guard = true;
}

async function wait_for_main_section(wrapper, retries = 12, delay_ms = 50) {
	for (let i = 0; i < retries; i++) {
		const $parent = $(wrapper).find(".layout-main-section");
		if ($parent.length) return $parent;
		await new Promise((resolve) => setTimeout(resolve, delay_ms));
	}
	return null;
}

async function load_vue(wrapper) {
	const load_seq = ++gold_buyback_load_seq;
	const $parent = await wait_for_main_section(wrapper);
	if (!$parent || load_seq !== gold_buyback_load_seq) return;

	try {
		$parent.html('<div id="anygold-gold-buyback-root"></div>');
		const $root = $parent.find("#anygold-gold-buyback-root");
		if (!$root.length) {
			throw new Error("Gold Buyback mount root not found.");
		}

		unmount_stale_gold_buyback_app();

		await ensure_gold_buyback_setup_loaded();
		if (load_seq !== gold_buyback_load_seq) return;

		frappe.gold_buyback_app = frappe.ui.setup_gold_buyback($root);
	} catch (e) {
		console.error("Gold Buyback mount failed", e);
		const err_msg = e && e.message ? e.message : String(e);
		$parent.html(`
			<div style="padding: 16px;">
				<div style="font-weight: 600; margin-bottom: 6px;">Failed to load Gold Buyback page.</div>
				<div style="font-size: 12px; color: var(--text-muted);">Please refresh the page. If this keeps happening, contact support.</div>
				<div style="font-size: 11px; color: var(--text-subtle); margin-top: 6px;">${frappe.utils.escape_html(err_msg)}</div>
			</div>
		`);
	}
}

function unmount_stale_gold_buyback_app() {
	if (!frappe.gold_buyback_app || typeof frappe.gold_buyback_app.unmount !== "function") return;

	try {
		frappe.gold_buyback_app.unmount();
	} catch (e) {
		console.warn("Gold Buyback stale app unmount failed", e);
	} finally {
		frappe.gold_buyback_app = null;
	}
}

async function ensure_gold_buyback_setup_loaded() {
	if (typeof frappe.ui.setup_gold_buyback === "function") return;

	const load_errors = [];
	for (const bundle_path of GOLD_BUYBACK_BUNDLE_PATHS) {
		try {
			await frappe.require(bundle_path);

			// Allow setup registration to settle after script eval.
			for (let i = 0; i < 8 && typeof frappe.ui.setup_gold_buyback !== "function"; i++) {
				await new Promise((resolve) => setTimeout(resolve, 40));
			}

			if (typeof frappe.ui.setup_gold_buyback === "function") return;
			load_errors.push(`[${bundle_path}] loaded but setup function missing`);
		} catch (err) {
			const msg = err && err.message ? err.message : String(err);
			load_errors.push(`[${bundle_path}] ${msg}`);
		}
	}

	throw new Error(`Unable to load Gold Buyback bundle. ${load_errors.join(" | ")}`);
}
