<template>
  <!-- ONE card, two-col — exactly matching original mockup structure -->
  <div class="card">
    <div class="two-col">

      <!-- ── LEFT: CUSTOMER ── -->
      <div class="two-col-left">
        <div class="section-label">Customer</div>

        <div class="field" style="margin-bottom: 12px">
          <label>Customer <span class="req">*</span></label>
          <div class="search-wrapper">
            <input type="text" class="field-input" style="text-transform: uppercase"
              placeholder="Search by name or IC..."
              :value="gb.cust.value ? gb.cust.value.name : gb.search.value"
              @input="e => { gb.search.value = e.target.value.toUpperCase(); gb.cust.value = null; gb.showDD.value = true }"
              @focus="() => gb.showDD.value = true"
            />
            <div v-if="gb.showDD.value" class="cust-dd">
              <div class="cust-scroll">
                <div v-for="c in filteredCustomers" :key="c.customer_id || c.ic || c.name" class="cust-item" @mousedown.prevent="gb.pickCust(c)">
                  <div class="cust-name">{{ c.name }}</div>
                  <div class="cust-meta">IC: {{ c.ic }} · {{ c.type }}
                    <span v-if="c.advance > 0" style="color: var(--green); font-weight: 600"> · Advance: RM {{ fmtRM(c.advance) }}</span>
                    <span v-if="c.locks > 0" style="color: var(--gold); font-weight: 600"> · 🔒 {{ c.locks }} Rate Lock{{ c.locks > 1 ? 's' : '' }}</span>
                  </div>
                </div>
              </div>
              <div class="cust-add" @mousedown.prevent="gb.showNewCust.value = true; gb.showDD.value = false">＋ Add New Customer</div>
            </div>
          </div>
        </div>

        <div class="grid-2" style="gap: 10px; margin-bottom: 10px">
          <div class="field">
            <label>IC Number</label>
            <input type="text" class="field-input" :value="gb.cust.value?.ic || ''" placeholder="Auto-filled" disabled />
          </div>
          <div class="field">
            <label>Mobile</label>
            <input type="text" class="field-input" :value="gb.cust.value ? fmtMobileStr(gb.cust.value.mobile) : ''" placeholder="Auto-filled" disabled />
          </div>
        </div>

        <div class="grid-2" style="gap: 10px">
          <div class="field">
            <label>Customer Type</label>
            <input type="text" class="field-input" :value="gb.cust.value?.type || ''" placeholder="Auto-filled" disabled />
          </div>
          <!-- Bank only shows when pm=bank AND customer has bank details -->
          <div v-if="gb.pm.value === 'bank' && gb.cust.value?.bank" class="field">
            <label>Bank</label>
            <input type="text" class="field-input" :value="gb.cust.value.bank" disabled />
          </div>
        </div>

        <!-- Bank Account only shows when pm=bank AND customer has acc -->
        <div v-if="gb.pm.value === 'bank' && gb.cust.value?.acc" class="field" style="margin-top: 10px">
          <label>Bank Account</label>
          <input type="text" class="field-input" :value="gb.cust.value.acc" disabled />
        </div>
      </div>

      <!-- ── RIGHT: PAYMENT ── -->
      <div class="two-col-right">
        <div class="section-label">Payment</div>

        <!-- Customer Account Balance sits in PAYMENT column — matches original -->
        <!-- positive=AR (they owe us), negative=AP (we owe them)
             ⚠️ MRADUL: replace cust.advance with frappe.call get_party_balance -->
        <div class="field" style="margin-bottom: 12px">
          <label style="display: flex; align-items: baseline; gap: 6px">
            Customer Account Balance
            <span v-if="gb.cust.value"
              style="font-size: 10px; font-weight: 400; text-transform: none; letter-spacing: 0"
              :style="{ color: gb.cust.value.advance > 0 ? 'var(--green)' : 'var(--text-subtle)' }">
              {{ gb.cust.value.advance > 0 ? '(they owe us)' : gb.cust.value.advance < 0 ? '(we owe them)' : '' }}
            </span>
          </label>
          <div class="advance-display">
            <span style="font-size: 12px; color: var(--text-muted)">
              {{ gb.custAcctAmt.value > 0 ? 'After this transaction:' : 'Current balance' }}
            </span>
            <span :class="['adv-amount', balanceClass]"
              :style="projectedNegative ? { color: 'var(--red)', fontWeight: 600 } : {}">
              {{ balanceDisplay }}
            </span>
          </div>
        </div>

        <div class="field" style="margin-bottom: 12px">
          <label>Payment Method <span class="req">*</span></label>
          <div class="pm-tabs">
            <div v-for="m in ['bank', 'cash', 'custacct', 'mix']" :key="m"
              :class="['pm-tab', gb.pm.value === m ? 'active' : '']"
              @click="gb.pm.value = m">{{ PM_LABELS[m] }}</div>
          </div>
        </div>

        <!-- BANK -->
        <div v-if="gb.pm.value === 'bank'" class="field" style="margin-bottom: 12px">
          <label>Account Paid From <span class="req">*</span></label>
          <select class="field-input" :value="gb.bankAccount.value" @change="e => gb.bankAccount.value = e.target.value">
            <option value="">Select account...</option>
            <option v-for="acc in gb.bankAccounts.value" :key="acc.value" :value="acc.value">{{ acc.label }}</option>
          </select>
        </div>

        <!-- CASH -->
        <div v-if="gb.pm.value === 'cash'" class="field" style="margin-bottom: 12px">
          <label>Cash Drawer Balance</label>
          <div class="advance-display">
            <span style="font-size: 12px; color: var(--text-muted)">Available in drawer</span>
            <span :class="['adv-amount', gb.gt.value > MOCK_CASH_BALANCE ? '' : gb.gt.value > 0 ? 'adv-positive' : 'adv-zero']"
              :style="gb.gt.value > MOCK_CASH_BALANCE ? { color: 'var(--red)', fontWeight: 600 } : {}">
              RM {{ fmtRM(MOCK_CASH_BALANCE) }}
            </span>
          </div>
          <div v-if="gb.gt.value > MOCK_CASH_BALANCE" class="info-box info-red" style="margin-top: 8px; margin-bottom: 0">
            ⚠️ Grand total exceeds cash drawer balance by RM {{ fmtRM(gb.gt.value - MOCK_CASH_BALANCE) }}
          </div>
        </div>

        <!-- CUSTOMER ACCOUNT -->
        <div v-if="gb.pm.value === 'custacct'" class="info-box info-blue">
          Full amount posts to Customer AP ledger. Auto-netting JE will net against any existing AR balance.
        </div>

        <!-- MIX -->
        <template v-if="gb.pm.value === 'mix'">
          <table class="mix-tbl">
            <thead><tr><th>Mode of Payment</th><th style="text-align: right">Amount (RM)</th><th style="width: 28px"></th></tr></thead>
            <tbody>
              <tr v-for="row in gb.mixRows.value" :key="row.id">
                <td>
                  <select :value="row.mode" @change="e => gb.updateMixRow(row.id, 'mode', e.target.value)">
                    <option>Cash</option><option>Bank Transfer</option><option>Customer Account</option>
                  </select>
                  <select
                    v-if="row.mode === 'Bank Transfer'"
                    style="margin-top: 6px"
                    :value="row.bank_account || ''"
                    @change="e => gb.updateMixRow(row.id, 'bank_account', e.target.value)"
                  >
                    <option value="">Select bank account...</option>
                    <option v-for="acc in gb.bankAccounts.value" :key="acc.value" :value="acc.value">{{ acc.label }}</option>
                  </select>
                </td>
                <td><input type="text" class="num-input" placeholder="0.00" :value="row.amount"
                  @input="e => gb.updateMixRow(row.id, 'amount', e.target.value.replace(/[^0-9.,]/g, ''))"
                  @blur="e => { const v = parseFloat(e.target.value.replace(/,/g, '')); gb.updateMixRow(row.id, 'amount', isNaN(v) ? '' : fmtRM(v)) }"
                  @keydown.enter="e => e.target.blur()" /></td>
                <td><button class="del-btn" @click="gb.removeMixRow(row.id)">✕</button></td>
              </tr>
            </tbody>
            <tbody>
              <tr class="total-row"><td>Total Entered</td><td style="text-align: right">RM {{ fmtRM(gb.mixTot.value) }}</td><td></td></tr>
              <tr class="total-row"><td>Invoice Total</td><td style="text-align: right">RM {{ fmtRM(gb.gt.value) }}</td><td></td></tr>
              <tr class="diff-row">
                <td style="color: var(--text-muted)">Difference</td>
                <td style="text-align: right">
                  <span v-if="Math.abs(gb.mixDiff.value) < 0.005" class="ok-badge">✓ Balanced</span>
                  <span v-else class="warn-badge">⚠ {{ gb.mixDiff.value > 0 ? '+' : '' }}RM {{ fmtRM(Math.abs(gb.mixDiff.value)) }}</span>
                </td>
                <td></td>
              </tr>
            </tbody>
          </table>
          <span class="add-link" @click="gb.addMixRow()">+ Add Payment Method</span>
        </template>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { fmtRM, fmtMobileStr } from '../../../utils/formatters.js'
import { PM_LABELS, MOCK_CASH_BALANCE } from '../../../constants/index.js'

const gb = inject('gb')

/* ---------------- CUSTOMER SEARCH ---------------- */

const customers = ref([])
const loadedBaseCustomers = ref(false)

const fetchCustomers = async () => {
  const res = await frappe.call({
    method: "frappe.client.get_list",
    args: {
      doctype: "Customer",
      fields: [
        "name",
        "customer_name",
        "mobile_no",
        "customer_group",
        "territory"
      ],
      order_by: "modified desc",
      limit_page_length: 5
    }
  })

  return res.message || []
}

const loadBaseCustomers = async () => {
  if (loadedBaseCustomers.value) return
  const data = await fetchCustomers()

  // Fetch balances for each customer
  const customersWithBalances = await Promise.all(data.map(async (c) => {
    const balance = await getCustomerBalance(c.name)
    return {
      name: c.customer_name,
      customer_id: c.name,
      ic: "",
      mobile: c.mobile_no || "",
      type: c.customer_group,
      bank: "",
      acc: "",
      advance: balance,
      locks: 0
    }
  }))

  customers.value = customersWithBalances
  loadedBaseCustomers.value = true
}

const filteredCustomers = computed(() => {
  const q = (gb.search.value || "").trim().toUpperCase()
  if (!q) return customers.value
  return customers.value.filter(c =>
    (c.name || "").toUpperCase().includes(q) ||
    (c.ic || "").toUpperCase().includes(q)
  )
})

watch(() => gb.showDD.value, async (isOpen) => {
  if (isOpen) await loadBaseCustomers()
})

/* ---------------- PICK CUSTOMER ---------------- */

const getCustomerBalance = async (customer) => {
  try {
    const res = await frappe.call({
      method: "erpnext.accounts.utils.get_balance_on",
      args: {
        party_type: "Customer",
        party: customer
      }
    })
    return res.message || 0
  } catch (e) {
    return 0
  }
}

gb.pickCust = async (c) => {
  gb.cust.value = c
  gb.search.value = c.name
  gb.showDD.value = false

  // Balance already fetched in the list
}

/* ---------------- BALANCE CALC ---------------- */

const projectedBalance  = computed(() => (gb.cust.value?.advance || 0) - gb.custAcctAmt.value)
const projectedNegative = computed(() => gb.custAcctAmt.value > 0 && projectedBalance.value < 0)

const balanceClass = computed(() => {
  if (gb.custAcctAmt.value > 0) return projectedBalance.value >= 0 ? 'adv-positive' : ''
  return (gb.cust.value?.advance || 0) > 0 ? 'adv-positive' : 'adv-zero'
})

const balanceDisplay = computed(() => {
  if (gb.custAcctAmt.value > 0) {
    const pb = projectedBalance.value
    return `RM ${fmtRM(Math.abs(pb))} ${pb >= 0 ? '(they owe us)' : '(we owe them)'}`
  }
  const adv = gb.cust.value?.advance || 0
  return `RM ${fmtRM(Math.abs(adv))}${adv > 0 ? ' AR' : adv < 0 ? ' AP' : ''}`
})
</script>

