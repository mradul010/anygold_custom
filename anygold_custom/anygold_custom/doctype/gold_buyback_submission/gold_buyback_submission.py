import frappe
from frappe.utils import flt, now_datetime
from erpnext.controllers.stock_controller import StockController

_PUR_SERIES_KEY   = "PUR-"
_PUR_SERIES_START = 124   # counter is seeded at 124 so first issued number is 125


class GoldBuybackSubmission(StockController):

	def autoname(self):
		dt = now_datetime()
		date_str = dt.strftime("%d%m%y")   # DDMMYY e.g. 080526

		# Atomically increment the series counter; seed at _PUR_SERIES_START if new.
		existing = frappe.db.sql(
			"SELECT `current` FROM `tabSeries` WHERE `name` = %s FOR UPDATE",
			(_PUR_SERIES_KEY,)
		)
		if existing:
			frappe.db.sql(
				"UPDATE `tabSeries` SET `current` = `current` + 1 WHERE `name` = %s",
				(_PUR_SERIES_KEY,)
			)
			next_num = int(existing[0][0]) + 1
		else:
			next_num = _PUR_SERIES_START + 1   # 125
			frappe.db.sql(
				"INSERT INTO `tabSeries` (`name`, `current`) VALUES (%s, %s)",
				(_PUR_SERIES_KEY, next_num)
			)

		self.name = f"PUR-{date_str}-{str(next_num).zfill(3)}"

	def validate(self):
		# AccountsController/StockController validators iterate self.items expecting
		# standard ERPNext fields (qty, t_warehouse, …) that our child table doesn't have.
		# We skip all parent validators and run only what applies to this doctype.
		for item in self.items:
			if flt(item.net_weight) <= 0:
				frappe.throw(frappe._("Row {0}: Net Weight cannot be zero").format(item.idx))

	def on_submit(self):
		self.update_stock_ledger()
		self.make_gl_entries()

	def on_cancel(self):
		self.update_stock_ledger()
		self.make_gl_entries_on_cancel()

	# ── GL Entries ─────────────────────────────────────────────────────────────

	def get_gl_entries(self, warehouse_account=None):
		gl_entries = []
		party_info = {"party_type": "Customer", "party": self.customer}
		voucher_label = {"custom_voucher_label": "Purchase (Gold Buyback)"}

		# Dr: Inventory account — no party (not a Receivable/Payable account).
		gl_entries.append(
			self.get_gl_dict({
				"account": self.inventory_account,
				"debit": flt(self.grand_total),
				"credit": 0,
				"cost_center": self.cost_center,
				"against": self._payment_against_str(),
				"remarks": f"Gold Buyback from {self.customer_name}",
				**voucher_label,
			})
		)

		# Cr: One line per payment method (mix = multiple lines).
		# party_type/party only on Receivable (Customer Account) lines.
		if self.payment_method == "mix":
			for row in self.mix_payments:
				if not row.account or flt(row.amount) <= 0:
					continue
				entry = {
					"account": row.account,
					"debit": 0,
					"credit": flt(row.amount),
					"cost_center": self.cost_center,
					"against": self.inventory_account,
					"remarks": f"Gold Buyback from {self.customer_name} ({row.mode})",
					**voucher_label,
				}
				if row.mode == "Customer Account":
					entry.update(party_info)
				gl_entries.append(self.get_gl_dict(entry))
		else:
			entry = {
				"account": self.payment_account,
				"debit": 0,
				"credit": flt(self.grand_total),
				"cost_center": self.cost_center,
				"against": self.inventory_account,
				"remarks": f"Gold Buyback from {self.customer_name}",
				**voucher_label,
			}
			if self.payment_method == "custacct":
				entry.update(party_info)
			gl_entries.append(self.get_gl_dict(entry))

		return gl_entries

	def _payment_against_str(self):
		if self.payment_method == "mix":
			return ", ".join(r.account for r in self.mix_payments if r.account)
		return self.payment_account or ""

	# ── Stock Ledger Entries ────────────────────────────────────────────────────

	def update_stock_ledger(self):
		sl_entries = []
		for item in self.items:
			if not item.item_code or not item.warehouse or flt(item.net_weight) <= 0:
				continue
			# On cancel (docstatus == 2), reverse the qty.
			actual_qty = flt(item.net_weight) * (-1 if self.docstatus == 2 else 1)
			sl_entries.append(
				self.get_sl_entries(item, {
					"actual_qty": actual_qty,
					"incoming_rate": flt(item.rate) if self.docstatus != 2 else 0,
				})
			)
		if sl_entries:
			from erpnext.stock.stock_ledger import make_sl_entries
			make_sl_entries(sl_entries)
			self._backfill_sle_descriptions()

	def _backfill_sle_descriptions(self):
		"""Write item description directly onto the SLE rows after creation."""
		for item in self.items:
			if not item.item_code or not item.warehouse or not item.description:
				continue
			frappe.db.sql(
				"""UPDATE `tabStock Ledger Entry`
				   SET `custom_description` = %s
				   WHERE `voucher_type` = %s
				     AND `voucher_no`   = %s
				     AND `voucher_detail_no` = %s""",
				(item.description, self.doctype, self.name, item.name),
			)

	def get_sl_entries(self, d, args):
		from erpnext.accounts.utils import get_fiscal_year
		fiscal_year = get_fiscal_year(self.posting_date, company=self.company)[0]

		sl_dict = frappe._dict({
			"item_code": d.item_code,
			"warehouse": d.warehouse,
			"posting_date": self.posting_date,
			"posting_time": self.posting_time or "00:00:00",
			"voucher_type": self.doctype,
			"voucher_no": self.name,
			"voucher_detail_no": d.name,
			"company": self.company,
			"fiscal_year": fiscal_year,
			"is_cancelled": 1 if self.docstatus == 2 else 0,
		})
		sl_dict.update(args)
		return sl_dict
