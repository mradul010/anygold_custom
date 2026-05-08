frappe.pages["customer-list"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: "AG Contacts",
		single_column: true,
	});
};

frappe.pages["customer-list"].on_page_show = async function (wrapper) {
	await load_ag_contact_list_vue(wrapper);
};

const AG_CONTACT_LIST_BUNDLE_KEY = "ag_contact_list.bundle.js";
const AG_CONTACT_LIST_BUNDLE_PATHS = [
	"/assets/anygold_custom/modules/ag-contact/ag_contact_list.bundle.js",
	"/assets/anygold_custom/js/ag_contact_list.bundle.js",
	"/assets/anygold_custom/dist/js/ag_contact_list.bundle.js",
	"/assets/anygold_custom/ag_contact_list.bundle.js",
];
const AG_CONTACT_LIST_SCRIPT_ID = "anygold-ag-contact-list-bundle-script";
let ag_contact_list_load_seq = 0;

async function wait_for_main_section_ag(wrapper, retries = 12, delay_ms = 50) {
	for (let i = 0; i < retries; i++) {
		const $parent = $(wrapper).find(".layout-main-section");
		if ($parent.length) return $parent;
		await new Promise((resolve) => setTimeout(resolve, delay_ms));
	}
	return null;
}

async function load_ag_contact_list_vue(wrapper) {
	const load_seq = ++ag_contact_list_load_seq;
	const $parent = await wait_for_main_section_ag(wrapper);
	if (!$parent || load_seq !== ag_contact_list_load_seq) return;

	try {
		$parent.html('<div id="anygold-ag-contact-list-root"></div>');
		const $root = $parent.find("#anygold-ag-contact-list-root");
		if (!$root.length) {
			throw new Error("AG Contact List mount root not found.");
		}

		unmount_stale_ag_contact_list_app();

		await ensure_ag_contact_list_setup_loaded();
		if (load_seq !== ag_contact_list_load_seq) return;

		frappe.ag_contact_list_app = frappe.ui.setup_ag_contact_list($root);
	} catch (e) {
		console.error("AG Contact List mount failed", e);
		const err_msg = e && e.message ? e.message : String(e);
		$parent.html(
			"<div style='padding: 16px;'>" +
			"<div style='font-weight: 600; margin-bottom: 6px;'>Failed to load AG Contacts page.</div>" +
			"<div style='font-size: 12px; color: var(--text-muted);'>Please refresh the page.</div>" +
			"<div style='font-size: 11px; color: var(--text-subtle); margin-top: 6px;'>" + frappe.utils.escape_html(err_msg) + "</div>" +
			"</div>"
		);
	}
}

function unmount_stale_ag_contact_list_app() {
	if (!frappe.ag_contact_list_app || typeof frappe.ag_contact_list_app.unmount !== "function") return;

	try {
		frappe.ag_contact_list_app.unmount();
	} catch (e) {
		console.warn("AG Contact List stale app unmount failed", e);
	} finally {
		frappe.ag_contact_list_app = null;
	}
}

async function ensure_ag_contact_list_setup_loaded() {
	if (typeof frappe.ui.setup_ag_contact_list === "function") return;

	const mapped = frappe && frappe.boot && frappe.boot.assets_json && frappe.boot.assets_json[AG_CONTACT_LIST_BUNDLE_KEY];
	const bundle_paths = mapped ? [mapped].concat(AG_CONTACT_LIST_BUNDLE_PATHS) : AG_CONTACT_LIST_BUNDLE_PATHS;
	const seen = new Set();
	const load_errors = [];

	for (const bundle_path of bundle_paths) {
		if (!bundle_path || seen.has(bundle_path)) continue;
		seen.add(bundle_path);

		try {
			await load_ag_contact_list_script(bundle_path);

			for (let i = 0; i < 8 && typeof frappe.ui.setup_ag_contact_list !== "function"; i++) {
				await new Promise((resolve) => setTimeout(resolve, 40));
			}

			if (typeof frappe.ui.setup_ag_contact_list === "function") return;
			load_errors.push("[" + bundle_path + "] loaded but setup function missing");
		} catch (err) {
			const msg = err && err.message ? err.message : String(err);
			load_errors.push("[" + bundle_path + "] " + msg);
		}
	}

	throw new Error("Unable to load AG Contact List bundle. " + load_errors.join(" | "));
}

function load_ag_contact_list_script(src) {
	return new Promise((resolve, reject) => {
		const normalized = new URL(src, window.location.origin).toString();
		const existing = Array.from(document.querySelectorAll("script[data-ag-contact-list-bundle='1']"))
			.find(function (el) { return el.src === normalized; });

		if (existing) {
			if (existing.dataset.loaded === "1") return resolve();
			existing.addEventListener("load", function () { resolve(); }, { once: true });
			existing.addEventListener("error", function () { reject(new Error("Failed to load " + src)); }, { once: true });
			return;
		}

		const script = document.createElement("script");
		script.id = AG_CONTACT_LIST_SCRIPT_ID + "-" + Math.random().toString(36).slice(2, 8);
		script.src = normalized;
		script.async = true;
		script.dataset.agContactListBundle = "1";
		script.onload = function () {
			script.dataset.loaded = "1";
			resolve();
		};
		script.onerror = function () { reject(new Error("Failed to load " + src)); };
		document.head.appendChild(script);
	});
}
