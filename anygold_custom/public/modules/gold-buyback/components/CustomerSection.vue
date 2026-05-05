<template>
  <!-- ONE card, two-col -->
  <div class="card">
    <div class="two-col">

      <!-- ── LEFT: CUSTOMER ── -->
      <div class="two-col-left">
        <div class="section-label">Customer</div>

        <div class="field" style="margin-bottom: 12px">
          <label>Customer <span class="req">*</span></label>
          <div class="search-wrapper">
            <input
              type="text"
              class="field-input"
              style="text-transform: uppercase"
              placeholder="Search by name, IC or passport..."
              :value="gb.cust.value ? gb.cust.value.name : gb.search.value"
              @input="onSearchInput"
              @focus="onSearchFocus"
              @keydown.escape="gb.showDD.value = false"
            />
            <div v-if="gb.showDD.value" class="cust-dd">
              <div v-if="searchLoading" style="padding: 12px 14px; font-size: 12px; color: var(--text-muted)">Searching…</div>
              <div v-else class="cust-scroll">
                <div
                  v-for="c in customers"
                  :key="c.customer_id"
                  class="cust-item"
                  @mousedown.prevent="pickCustomer(c)"
                >
                  <div class="cust-name">{{ c.name }}</div>
                  <div class="cust-meta">
                    {{ c.nationality === 'Malaysian' ? 'IC' : 'PP' }}:
                    {{ c.ic || c.passport || '—' }} · {{ c.type }}
                    <span v-if="c.advance > 0" style="color: var(--green); font-weight: 600"> · Advance: RM {{ fmtRM(c.advance) }}</span>
                    <span v-if="c.locks > 0" style="color: var(--gold); font-weight: 600"> · 🔒 {{ c.locks }} Rate Lock{{ c.locks > 1 ? 's' : '' }}</span>
                  </div>
                </div>
                <div v-if="!customers.length && !searchLoading" style="padding: 12px 14px; font-size: 12px; color: var(--text-muted)">No customers found.</div>
              </div>
              <div class="cust-add" @mousedown.prevent="openNewCustModal">＋ Add New Customer</div>
            </div>
          </div>
        </div>

        <div class="grid-2" style="gap: 10px; margin-bottom: 10px">
          <div class="field">
            <label>{{ gb.cust.value?.nationality === 'Non-Malaysian / Foreigner' ? 'Passport No.' : 'IC Number' }}</label>
            <input type="text" class="field-input"
              :value="gb.cust.value?.nationality === 'Non-Malaysian / Foreigner' ? (gb.cust.value?.passport || '') : (gb.cust.value?.ic || '')"
              placeholder="Auto-filled" disabled />
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
          <div v-if="gb.pm.value === 'bank' && gb.cust.value?.bank" class="field">
            <label>Bank</label>
            <input type="text" class="field-input" :value="gb.cust.value.bank" disabled />
          </div>
        </div>

        <div v-if="gb.pm.value === 'bank' && gb.cust.value?.acc" class="field" style="margin-top: 10px">
          <label>Bank Account</label>
          <input type="text" class="field-input" :value="gb.cust.value.acc" disabled />
        </div>
      </div>

      <!-- ── RIGHT: PAYMENT ── -->
      <div class="two-col-right">
        <div class="section-label">Payment</div>

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

  <!-- ═══════════════════════════════════════════════════════════
       NEW CUSTOMER MODAL
       Teleported to <body> so it's never clipped by parent overflow.
       ═══════════════════════════════════════════════════════════ -->
  <teleport to="body">
    <div v-if="gb.showNewCust.value" class="gb-modal-overlay" @mousedown.self="closeNewCustModal">
      <div class="gb-modal-box" role="dialog" aria-modal="true" aria-labelledby="new-cust-title">

        <!-- Header -->
        <div class="gb-modal-header">
          <h3 id="new-cust-title">
            New Customer
            <span v-if="isMalaysian" class="nc-badge-malaysian">🇲🇾 Malaysian</span>
            <span v-else class="nc-badge-foreigner">🌍 Non-Malaysian</span>
          </h3>
          <button class="gb-modal-close" @click="closeNewCustModal" aria-label="Close">×</button>
        </div>

        <!-- Body -->
        <div class="gb-modal-body">

          <!-- Validation errors -->
          <div v-if="formErrors.length" class="nc-errors">
            <div v-for="e in formErrors" :key="e" class="nc-error">⚠ {{ e }}</div>
          </div>

          <!-- Customer Name -->
          <div class="nc-f">
            <label>Customer Name <span class="req">*</span></label>
            <input
              type="text"
              class="field-input"
              v-model="form.customer_name"
              placeholder="Full legal name"
              style="text-transform: uppercase"
              autocomplete="off"
            />
          </div>

          <!-- Nationality + Customer Type -->
          <div class="grid-2" style="gap: 12px">
            <div class="nc-f" style="margin-bottom: 0">
              <label>Nationality <span class="req">*</span></label>
              <select class="field-input" v-model="form.nationality" @change="onNationalityChange">
                <option value="Malaysian">Malaysian</option>
                <option value="Non-Malaysian / Foreigner">Non-Malaysian / Foreigner</option>
              </select>
            </div>
            <div class="nc-f" style="margin-bottom: 0">
              <label>Customer Type <span class="req">*</span></label>
              <select class="field-input" v-model="form.customer_type">
                <option>Individual</option>
                <option>Dealer</option>
                <option>Company</option>
              </select>
            </div>
          </div>

          <div class="nc-section-divider">Identity</div>

          <!-- IC Number — Malaysian only -->
          <div v-if="isMalaysian" class="nc-f">
            <label>IC Number <span class="req">*</span></label>
            <input
              type="text"
              class="field-input"
              v-model="form.ic_number"
              placeholder="e.g. 900101-14-1234"
              autocomplete="off"
            />
          </div>

          <!-- Passport / ID + Country — Non-Malaysian only -->
          <template v-if="!isMalaysian">
            <div class="nc-f">
              <label>Passport / ID Number <span class="req">*</span></label>
              <input
                type="text"
                class="field-input"
                v-model="form.other_id_number"
                placeholder="Passport or ID number"
                autocomplete="off"
              />
            </div>
            <div class="nc-f">
              <label>Country / ID Type <span class="req">*</span></label>
              <input
                type="text"
                class="field-input"
                v-model="form.other_id_type"
                placeholder="e.g. Singapore, India"
                autocomplete="off"
              />
            </div>
          </template>

          <div class="nc-section-divider">Contact</div>

          <!-- Mobile -->
          <div class="nc-f">
            <label>Mobile Number <span class="req">*</span></label>
            <input
              type="tel"
              class="field-input"
              v-model="form.mobile_no"
              placeholder="e.g. 0123456789"
              autocomplete="off"
            />
          </div>

          <div class="nc-section-divider">Banking (Optional)</div>

          <!-- Bank Name + Account Number -->
          <div class="grid-2" style="gap: 12px">
            <div class="nc-f" style="margin-bottom: 0">
              <label>Bank Name</label>
              <input type="text" class="field-input" v-model="form.bank_name" placeholder="e.g. Maybank" />
            </div>
            <div class="nc-f" style="margin-bottom: 0">
              <label>Account Number</label>
              <input type="text" class="field-input" v-model="form.bank_account_number" placeholder="Optional" />
            </div>
          </div>

          <div class="nc-section-divider">{{ photoLabel }}</div>

          <!-- Photo upload -->
          <div class="nc-f" style="margin-bottom: 0">
            <div
              :class="['nc-photo-upload', form.photo_url ? 'has-file' : '']"
              @click="triggerPhotoUpload"
            >
              <div v-if="photoUploading" class="nc-uploading">Uploading…</div>
              <template v-else-if="form.photo_url">
                <div class="nc-photo-icon">✅</div>
                <div class="nc-photo-name">{{ form.photo_filename }}</div>
              </template>
              <template v-else>
                <div class="nc-photo-icon">📎</div>
                <div class="nc-photo-hint">Click to upload JPG or PNG</div>
              </template>
            </div>
            <input
              ref="photoInputRef"
              type="file"
              accept="image/jpeg,image/png,image/jpg"
              style="display: none"
              @change="onPhotoSelect"
            />
          </div>

        </div>

        <!-- Footer -->
        <div class="gb-modal-footer">
          <button class="btn btn-outline" @click="closeNewCustModal" :disabled="saving">Cancel</button>
          <button class="btn btn-gold" @click="submitNewCustomer" :disabled="saving">
            {{ saving ? 'Saving…' : 'Save Customer' }}
          </button>
        </div>

      </div>
    </div>
  </teleport>
</template>

<script setup>
import { computed, inject, reactive, ref, watch } from 'vue'
import { fmtRM, fmtMobileStr } from '../../../utils/formatters.js'
import { PM_LABELS, MOCK_CASH_BALANCE } from '../../../constants/index.js'

const gb = inject('gb')

// ════════════════════════════════════════════════════════════════
// CUSTOMER SEARCH
// ════════════════════════════════════════════════════════════════

const customers          = ref([])
const loadedOnce         = ref(false)
const searchLoading      = ref(false)
let   searchDebounceTimer = null

/** Map a raw Customer doc row to the app's customer shape. */
const mapCustomer = async (c) => {
  const balance = await getCustomerBalance(c.name)
  return {
    name:        c.customer_name          || c.name,
    customer_id: c.name,
    ic:          c.malaysian_id           || '',
    passport:    c.other_id_number        || '',
    nationality: c.customer_nationality   || 'Malaysian',
    country:     c.other_id_type          || '',
    type:        c.customer_group         || 'Individual',
    mobile:      c.mobile_no              || '',
    bank:        c.bank_name              || '',
    acc:         c.bank_account_number    || '',
    advance:     balance,
    locks:       0,
  }
}

const fetchCustomers = async (query = '') => {
  searchLoading.value = true
  try {
    const res = await frappe.call({
      method: 'anygold_custom.api.GoldBuyBack.customer.search_goldbuyback_customers',
      args:   { query, limit: 20 },
    })
    const raw     = res.message || []
    customers.value = await Promise.all(raw.map(mapCustomer))
    if (!query) loadedOnce.value = true
  } catch (e) {
    console.warn('Customer search failed', e)
    customers.value = []
  } finally {
    searchLoading.value = false
  }
}

const debouncedSearch = (q) => {
  clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => fetchCustomers(q), 280)
}

const onSearchFocus = () => {
  gb.showDD.value = true
  if (!loadedOnce.value) fetchCustomers('')
}

const onSearchInput = (e) => {
  const val = e.target.value.toUpperCase()
  gb.search.value  = val
  gb.cust.value    = null
  gb.showDD.value  = true
  debouncedSearch(val)
}

watch(() => gb.showDD.value, (isOpen) => {
  if (isOpen && !loadedOnce.value) fetchCustomers('')
})

// ════════════════════════════════════════════════════════════════
// PICK CUSTOMER
// ════════════════════════════════════════════════════════════════

const getCustomerBalance = async (customerDocName) => {
  try {
    const res = await frappe.call({
      method: 'erpnext.accounts.utils.get_balance_on',
      args:   { party_type: 'Customer', party: customerDocName },
    })
    return res.message || 0
  } catch {
    return 0
  }
}

const pickCustomer = (c) => {
  gb.cust.value    = c
  gb.search.value  = c.name
  gb.showDD.value  = false
  // Reuse the composable's MOCK_LOCKS for dealers until live lock fetch is wired
  gb.locks.value   = []
  gb.validationErrors.value = []
}

// Override composable's pickCust so search-list clicks work too
gb.pickCust = pickCustomer

// ════════════════════════════════════════════════════════════════
// BALANCE DISPLAY
// ════════════════════════════════════════════════════════════════

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

// ════════════════════════════════════════════════════════════════
// NEW CUSTOMER MODAL
// ════════════════════════════════════════════════════════════════

const saving         = ref(false)
const formErrors     = ref([])
const photoInputRef  = ref(null)
const photoUploading = ref(false)

const form = reactive({
  customer_name:        '',
  nationality:          'Malaysian',
  customer_type:        'Individual',
  mobile_no:            '',
  ic_number:            '',   // Malaysian IC — submitted as 'malaysian_id'
  other_id_type:        '',   // Non-Malaysian country/ID type — matches DB field 'other_id_type'
  other_id_number:      '',   // Non-Malaysian passport/ID — matches DB field 'other_id_number'
  bank_name:            '',
  bank_account_number:  '',
  photo_url:            '',
  photo_filename:       '',
})

// ── Computed helpers ──
const isMalaysian    = computed(() => form.nationality === 'Malaysian')
const photoLabel     = computed(() => isMalaysian.value ? 'Customer IC Photo (Optional)' : 'Passport / ID Photo (Optional)')

// ── Nationality change: clear irrelevant fields ──
const onNationalityChange = () => {
  if (isMalaysian.value) {
    form.other_id_type   = ''
    form.other_id_number = ''
  } else {
    form.ic_number = ''
  }
}

// ── Modal open/close ──
const openNewCustModal = () => {
  gb.showDD.value       = false
  gb.showNewCust.value  = true
}

const closeNewCustModal = () => {
  if (saving.value) return
  gb.showNewCust.value  = false
  formErrors.value      = []
  // Reset form
  Object.assign(form, {
    customer_name: '', nationality: 'Malaysian', customer_type: 'Individual',
    mobile_no: '', ic_number: '', other_id_type: '', other_id_number: '',
    bank_name: '', bank_account_number: '', photo_url: '', photo_filename: '',
  })
  if (photoInputRef.value) photoInputRef.value.value = ''
}

// ── Photo upload ──
const triggerPhotoUpload = () => photoInputRef.value?.click()

const onPhotoSelect = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return

  form.photo_filename = file.name
  photoUploading.value = true

  try {
    const fd = new FormData()
    fd.append('file', file, file.name)
    fd.append('is_private', '0')
    fd.append('folder', 'Home/Attachments')

    const res  = await fetch('/api/method/upload_file', {
      method:  'POST',
      body:    fd,
      headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token },
    })
    const data = await res.json()
    form.photo_url = data.message?.file_url || ''
  } catch (err) {
    console.warn('Photo upload failed:', err)
    // Keep filename but no URL — backend will receive empty string
  } finally {
    photoUploading.value = false
  }
}

// ── Validation ──
const validateForm = () => {
  const errs = []
  if (!form.customer_name.trim())  errs.push('Customer Name is required.')
  if (!form.nationality)           errs.push('Nationality is required.')
  if (!form.customer_type)         errs.push('Customer Type is required.')
  if (!form.mobile_no.trim())      errs.push('Mobile Number is required.')

  if (isMalaysian.value) {
    if (!form.ic_number.trim())       errs.push('IC Number is required for Malaysian customers.')
  } else {
    if (!form.other_id_number.trim()) errs.push('Passport / ID Number is required.')
    if (!form.other_id_type.trim())   errs.push('Country / ID Type is required.')
  }
  return errs
}

// ── Build backend payload ──
const buildPayload = () => {
  const p = {
    customer_name:       form.customer_name.trim().toUpperCase(),
    nationality:         form.nationality,
    customer_type:       form.customer_type,
    mobile_no:           form.mobile_no.trim(),
    bank_name:           form.bank_name.trim(),
    bank_account_number: form.bank_account_number.trim(),
    customer_photo:      form.photo_url,
  }
  if (isMalaysian.value) {
    p.malaysian_id    = form.ic_number.trim()
    p.other_id_type   = ''
    p.other_id_number = ''
  } else {
    p.malaysian_id    = ''
    p.other_id_type   = form.other_id_type.trim()
    p.other_id_number = form.other_id_number.trim()
  }
  return p
}

// ── Submit ──
const submitNewCustomer = async () => {
  const errs = validateForm()
  if (errs.length) { formErrors.value = errs; return }
  formErrors.value = []
  saving.value     = true

  try {
    const res  = await frappe.call({
      method: 'anygold_custom.api.GoldBuyBack.customer.create_goldbuyback_customer',
      args:   { data: JSON.stringify(buildPayload()) },
    })
    const data = res.message

    if (!data?.success) {
      formErrors.value = [data?.message || 'Failed to save customer.']
      return
    }

    if (data.duplicate) {
      frappe.show_alert({ message: data.message, indicator: 'orange' }, 6)
    } else {
      frappe.show_alert({ message: 'Customer saved successfully!', indicator: 'green' }, 4)
    }

    // Map backend response → app customer shape
    // _customer_response returns: nationality, ic_number, passport_number, country, bank_name, bank_account_number
    const c = data.customer
    const custObj = {
      name:        c.customer_name          || '',
      customer_id: c.name,
      ic:          c.ic_number              || '',
      passport:    c.passport_number        || '',
      nationality: c.nationality            || 'Malaysian',
      country:     c.country               || '',
      type:        c.customer_group         || form.customer_type,
      mobile:      c.mobile_no              || form.mobile_no,
      bank:        c.bank_name              || '',
      acc:         c.bank_account_number    || '',
      advance:     0,
      locks:       0,
    }

    // Select the new customer
    pickCustomer(custObj)

    // Prepend to the customer list so it shows immediately if DD reopened
    if (!customers.value.find(x => x.customer_id === custObj.customer_id)) {
      customers.value = [custObj, ...customers.value]
    }
    loadedOnce.value = false // force a fresh fetch next DD open

    closeNewCustModal()

  } catch (err) {
    formErrors.value = [err.message || 'An unexpected error occurred. Please try again.']
  } finally {
    saving.value = false
  }
}
</script>
