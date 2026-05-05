import frappe
from frappe.utils import flt
from erpnext.controllers.stock_controller import StockController


class GoldBuybackSubmission(StockController):

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

		# Dr: Inventory account — one consolidated line for the full grand total.
		gl_entries.append(
			self.get_gl_dict({
				"account": self.inventory_account,
				"debit": flt(self.grand_total),
				"credit": 0,
				"cost_center": self.cost_center,
				"against": self._payment_against_str(),
				"remarks": f"Gold Buyback from {self.customer_name}",
			})
		)

		# Cr: One line per payment method (mix = multiple lines).
		if self.payment_method == "mix":
			for row in self.mix_payments:
				if not row.account or flt(row.amount) <= 0:
					continue
				entry = self.get_gl_dict({
					"account": row.account,
					"debit": 0,
					"credit": flt(row.amount),
					"cost_center": self.cost_center,
					"against": self.inventory_account,
					"remarks": f"Gold Buyback from {self.customer_name} ({row.mode})",
				})
				if row.mode == "Customer Account":
					entry.update({"party_type": "Customer", "party": self.customer})
				gl_entries.append(entry)
		else:
			entry = self.get_gl_dict({
				"account": self.payment_account,
				"debit": 0,
				"credit": flt(self.grand_total),
				"cost_center": self.cost_center,
				"against": self.inventory_account,
				"remarks": f"Gold Buyback from {self.customer_name}",
			})
			if self.payment_method == "custacct":
				entry.update({"party_type": "Customer", "party": self.customer})
			gl_entries.append(entry)

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
