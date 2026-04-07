frappe.pages['gold-buyback'].on_page_load = function(wrapper) {

	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Gold Buyback',
		single_column: true
	});

	const $body = $(page.body);

	$body.append(`
	<div class="gb-app">

		<div class="gb-main">

			<!-- LEFT -->
			<div class="gb-left">

				${header_section()}
				${customer_payment_section()}
				${bag_section()}
				${items_section()}

			</div>

			<!-- RIGHT -->
			<div class="gb-right">

				${summary_section()}
				${transaction_section()}

			</div>

		</div>

	</div>
	`);

	// Add row
	$body.on('click', '#add-row', function () {
		let count = $('#items-body tr').length + 1;

		$('#items-body').append(`
			<tr>
				<td>${count}</td>
				<td><input class="gb-table-input" placeholder="Item"/></td>
				<td><input class="gb-table-input" value="916"/></td>
				<td><input class="gb-table-input"/></td>
				<td><input class="gb-table-input"/></td>
				<td><input class="gb-table-input"/></td>
				<td><input class="gb-table-input" readonly/></td>
				<td><button class="gb-delete">×</button></td>
			</tr>
		`);
	});

	// Remove row
	$body.on('click', '.gb-delete', function () {
		$(this).closest('tr').remove();
	});

};


/* ================= SECTIONS ================= */

function header_section() {
	return `
	<div class="gb-card">

		<div class="gb-title">Purchase Details</div>

		<div class="gb-grid-4">

			<input class="gb-input" value="AUTO" placeholder="Series" readonly />
			<input type="date" class="gb-input"/>
			<input class="gb-input" value="Your Company"/>
			<input type="time" class="gb-input"/>

		</div>

	</div>
	`;
}


function customer_payment_section() {
	return `
	<div class="gb-card">

		<div class="gb-grid-2">

			<!-- CUSTOMER -->
			<div>
				<div class="gb-title">Customer</div>

				<input class="gb-input w-100" placeholder="Search customer"/>

				<div class="gb-grid-2 mt-2">
					<input class="gb-input" placeholder="IC Number"/>
					<input class="gb-input" placeholder="Mobile"/>
				</div>
			</div>

			<!-- PAYMENT -->
			<div>
				<div class="gb-title">Payment</div>

				<div class="gb-pill-group">
					<div class="gb-pill active">Cash</div>
					<div class="gb-pill">Bank</div>
					<div class="gb-pill">UPI</div>
					<div class="gb-pill">Mix</div>
				</div>

				<div class="gb-box mt-2">
					Available Advance
					<span>RM 0.00</span>
				</div>
			</div>

		</div>

	</div>
	`;
}


function bag_section() {
	return `
	<div class="gb-card">

		<div class="gb-title">Bag Destination</div>

		<select class="gb-input">
			<option>WS-Main Bag</option>
		</select>

	</div>
	`;
}


function items_section() {
	return `
	<div class="gb-card">

		<div class="gb-title">Items</div>

		<table class="gb-table">
			<thead>
				<tr>
					<th>#</th>
					<th>Description</th>
					<th>Purity</th>
					<th>Gross</th>
					<th>Net</th>
					<th>Rate</th>
					<th>Amount</th>
					<th></th>
				</tr>
			</thead>

			<tbody id="items-body">
				<tr>
					<td>1</td>
					<td><input class="gb-table-input"/></td>
					<td><input class="gb-table-input" value="916"/></td>
					<td><input class="gb-table-input"/></td>
					<td><input class="gb-table-input"/></td>
					<td><input class="gb-table-input"/></td>
					<td><input class="gb-table-input" readonly/></td>
					<td><button class="gb-delete">×</button></td>
				</tr>
			</tbody>
		</table>

		<button id="add-row" class="gb-add">+ Add Item</button>

	</div>
	`;
}


function summary_section() {
	return `
	<div class="gb-card">

		<div class="gb-title">Summary</div>

		<div class="gb-row">
			<span>Total Weight</span>
			<span>0.000 g</span>
		</div>

		<div class="gb-row">
			<span>Total Amount</span>
			<span>RM 0.00</span>
		</div>

		<hr>

		<div class="gb-row">
			<span>Discount</span>
			<input class="gb-input small"/>
		</div>

		<hr>

		<div class="gb-total">
			<span>Grand Total</span>
			<span>RM 0.00</span>
		</div>

	</div>
	`;
}


function transaction_section() {
	return `
	<div class="gb-card">

		<div class="gb-title">Transaction</div>

		<div class="gb-row">
			<span>Total XAU</span>
			<span>0.000</span>
		</div>

		<div class="gb-row">
			<span>AVCO</span>
			<span>—</span>
		</div>

	</div>
	`;
}