<!--
  ── FRAPPE MOUNT EXAMPLE ──
  In your Frappe page JS file (e.g. gold_buyback.js), add:

  frappe.pages['gold-buyback'].on_page_show = async function(wrapper) {
    const $parent = $(wrapper).find('.layout-main-section')
    $parent.empty()
    await frappe.require('gold_buyback.bundle.js')
    frappe.ui.setup_gold_buyback($parent)
  }

  In your bundle file (e.g. gold_buyback.bundle.js), add:

  import { createApp } from 'vue'
  import GoldBuybackPage from './modules/gold-buyback/GoldBuybackPage.vue'

  frappe.ui.setup_gold_buyback = function(wrapper) {
    const app = createApp(GoldBuybackPage)
    app.mount(wrapper.get(0))
    return app
  }

  Then run: bench build
-->
<template>
  <!-- REVIEW VIEW -->
  <ReviewPage v-if="gb.view.value === 'review'" />

  <!-- SUBMITTED VIEW -->
  <SubmittedPage v-else-if="gb.view.value === 'submitted'" />

  <!-- DRAFT VIEW — MOBILE -->
  <div v-else-if="gb.isMobile.value" style="height: 100%; overflow-y: auto; background: var(--bg)">
    <!-- STICKY HEADER -->
    <div class="m-doc-hdr">
      <div class="m-hdr-r1">
        <button class="m-back">← Buyback</button>
        <div style="display: flex; align-items: center; gap: 6px">
          <span class="m-doc-title">New Purchase</span>
          <span :class="['status-badge', gb.status.value === 'draft' ? 'status-draft' : 'status-saved']">
            {{ gb.status.value === 'draft' ? 'Not Saved' : 'Saved' }}
          </span>
        </div>
        <button class="btn btn-primary" style="padding: 7px 14px; font-size: 13px" @click="gb.goReview()">Save</button>
      </div>
      <div class="m-hdr-r2">
        <span :class="['m-tog-lbl', !gb.niH.value ? 'active' : '']">Item in Hand</span>
        <label class="toggle-switch">
          <input type="checkbox" :checked="gb.niH.value" @change="e => gb.niH.value = e.target.checked" />
          <span class="toggle-track"></span>
        </label>
        <span :class="['m-tog-lbl', gb.niH.value ? 'active' : '']">Item Not In Hand</span>
      </div>
    </div>

    <!-- VALIDATION ERRORS -->
    <div v-if="gb.validationErrors.value.length"
      style="margin: 8px 10px 0; background: var(--red-light); border: 1px solid var(--red-border); border-radius: var(--radius); padding: 10px 12px">
      <div v-for="(e, i) in gb.validationErrors.value" :key="i"
        style="font-size: 12px; color: var(--red); display: flex; gap: 6px">
        <span style="font-weight: 700">⚠</span>{{ e }}
      </div>
    </div>

    <div class="m-scroll">
      <!-- DOCUMENT -->
      <div class="m-sec">
        <div class="m-sec-hdr" @click="gb.togSec('doc')">
          <div class="m-sec-hl">
            <span class="m-sec-ttl">Document</span>
            <span class="m-sec-note">{{ gb.docNo.value }}</span>
          </div>
          <span :class="['m-chev', gb.mSec.value.doc ? 'open' : '']">▶</span>
        </div>
        <div v-if="gb.mSec.value.doc" class="m-sec-body">
          <div class="m-g2">
            <div class="m-f"><label>Doc No.</label><div class="m-ro">{{ gb.docNo.value }}</div></div>
            <div class="m-f"><label>Date</label>
              <input type="date" class="field-input" :value="today" :disabled="!gb.editTime.value" />
            </div>
          </div>
          <div class="m-g2">
            <div class="m-f"><label>Posting Time</label>
              <input type="time" class="field-input" :value="gb.time.value" :disabled="!gb.editTime.value"
                @change="e => gb.time.value = e.target.value" />
            </div>
            <div class="m-f"><label>Company</label><div class="m-ro">Anygold Sdn. Bhd.</div></div>
          </div>
          <label style="display: flex; align-items: center; gap: 7px; font-size: 12px; color: var(--text-muted); cursor: pointer">
            <input type="checkbox" :checked="gb.editTime.value" @change="e => gb.editTime.value = e.target.checked"
              style="accent-color: var(--gold); width: 14px; height: 14px" />
            Edit Posting Date &amp; Time
          </label>
        </div>
      </div>

      <!-- CUSTOMER -->
      <div class="m-sec">
        <div class="m-sec-hdr" @click="gb.togSec('cust')">
          <div class="m-sec-hl">
            <span class="m-sec-ttl">Customer</span>
            <span v-if="gb.cust.value" class="m-sec-note ok">✓ {{ gb.cust.value.name }}</span>
            <span v-else class="m-sec-note warn">⚠ Required</span>
          </div>
          <span :class="['m-chev', gb.mSec.value.cust ? 'open' : '']">▶</span>
        </div>
        <div v-if="gb.mSec.value.cust" class="m-sec-body">
          <div class="m-f">
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
                  <div v-for="c in gb.filtCust.value" :key="c.ic" class="cust-item" @mousedown.prevent="gb.pickCust(c)">
                    <div class="cust-name">{{ c.name }}</div>
                    <div class="cust-meta">IC: {{ c.ic }} · {{ c.type }}
                      <span v-if="c.advance > 0" style="color: var(--green); font-weight: 600"> · AR: RM {{ fmtRM(c.advance) }}</span>
                      <span v-if="c.locks > 0" style="color: var(--gold); font-weight: 600"> · 🔒 {{ c.locks }}</span>
                    </div>
                  </div>
                </div>
                <div class="cust-add" @mousedown.prevent="gb.showNewCust.value = true; gb.showDD.value = false">＋ Add New Customer</div>
              </div>
            </div>
          </div>
          <div class="m-g2">
            <div class="m-f"><label>IC Number</label><div class="m-ro">{{ gb.cust.value?.ic || 'Auto-filled' }}</div></div>
            <div class="m-f"><label>Mobile</label><div class="m-ro">{{ gb.cust.value ? fmtMobileStr(gb.cust.value.mobile) : 'Auto-filled' }}</div></div>
          </div>
          <div class="m-f" style="margin-bottom: 12px">
            <label>Customer Type</label>
            <div class="m-ro">{{ gb.cust.value?.type || 'Auto-filled' }}</div>
          </div>
          <!-- Customer Account Balance -->
          <div class="m-f" style="margin-bottom: 0">
            <label style="display: flex; align-items: baseline; gap: 5px; flex-wrap: wrap">
              Customer Account Balance
              <span v-if="gb.cust.value" style="font-size: 10px; font-weight: 400; text-transform: none; letter-spacing: 0"
                :style="{ color: gb.cust.value.advance > 0 ? 'var(--green)' : gb.cust.value.advance < 0 ? 'var(--red)' : 'var(--text-subtle)' }">
                {{ gb.cust.value.advance > 0 ? '(they owe us)' : gb.cust.value.advance < 0 ? '(we owe them)' : '' }}
              </span>
            </label>
            <div class="m-adv">
              <span>{{ gb.custAcctAmt.value > 0 ? 'After:' : 'Current' }}</span>
              <span :style="{ fontWeight: 600, fontSize: '13px', color: gb.custAcctAmt.value > 0 && (gb.cust.value?.advance || 0) - gb.custAcctAmt.value < 0 ? 'var(--red)' : (gb.cust.value?.advance || 0) > 0 ? 'var(--green)' : 'var(--text-subtle)' }">
                {{ mobileBalanceDisplay }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- ITEMS -->
      <div class="m-sec">
        <div class="m-sec-hdr" @click="gb.togSec('items')">
          <div class="m-sec-hl">
            <span class="m-sec-ttl">Items</span>
            <span v-if="gb.itemSummary.value" class="m-sec-note ok">{{ gb.itemSummary.value }}</span>
            <span v-else class="m-sec-note warn">⚠ Required</span>
          </div>
          <span :class="['m-chev', gb.mSec.value.items ? 'open' : '']">▶</span>
        </div>
        <div v-if="gb.mSec.value.items" class="m-sec-body">
          <!-- Bag bar -->
          <div v-if="!gb.niH.value" class="m-bag-bar">
            <label>Default Bag</label>
            <select v-model="gb.defBag.value">
              <option v-for="b in BAG_OPTIONS" :key="b">{{ b }}</option>
            </select>
          </div>
          <div v-else style="padding: 8px 0 10px; border-bottom: 1px solid var(--border); margin-bottom: 10px; font-size: 12px; color: var(--text-muted); display: flex; align-items: center; gap: 6px">
            <span>📦</span> All items → WS-Not In Hand (auto-assigned)
          </div>
          <!-- Item cards -->
          <MobileItemCard
            v-for="(item, idx) in gb.items.value"
            :key="item.id"
            :item="item"
            :idx="idx"
            :isLastAdded="gb.lastAddedId.value === item.id"
          />
          <button class="m-add-btn" @click="gb.addItem()">＋ Add Item</button>
        </div>
      </div>

      <!-- PAYMENT -->
      <div class="m-sec">
        <div class="m-sec-hdr" @click="gb.togSec('pay')">
          <div class="m-sec-hl">
            <span class="m-sec-ttl">Payment</span>
            <span v-if="gb.pm.value" class="m-sec-note ok">✓ {{ PM_LABELS[gb.pm.value] }}</span>
            <span v-else class="m-sec-note warn">⚠ Required</span>
          </div>
          <span :class="['m-chev', gb.mSec.value.pay ? 'open' : '']">▶</span>
        </div>
        <div v-if="gb.mSec.value.pay" class="m-sec-body">
          <div class="m-f">
            <label>Payment Method <span class="req">*</span></label>
            <div class="m-pm-tabs">
              <div v-for="m in ['bank', 'cash', 'custacct', 'mix']" :key="m"
                :class="['m-pm-tab', gb.pm.value === m ? 'active' : '']"
                @click="gb.pm.value = m">{{ PM_LABELS[m] }}</div>
            </div>
          </div>
          <div v-if="gb.pm.value === 'bank'" class="m-f" style="margin-bottom: 0">
            <label>Account Paid From</label>
            <select class="field-input" :value="gb.bankAccount.value" @change="e => gb.bankAccount.value = e.target.value">
              <option value="">Select account...</option>
              <option v-for="acc in gb.bankAccounts.value" :key="acc.value" :value="acc.value">{{ acc.label }}</option>
            </select>
          </div>
          <div v-if="gb.pm.value === 'cash'">
            <div class="m-adv" style="margin-bottom: 6px">
              <span>Available in drawer</span>
              <span :style="{ fontWeight: 600, color: gb.gt.value > MOCK_CASH_BALANCE ? 'var(--red)' : 'var(--green)' }">RM {{ fmtRM(MOCK_CASH_BALANCE) }}</span>
            </div>
            <div v-if="gb.gt.value > MOCK_CASH_BALANCE" class="info-box info-red" style="margin-bottom: 0">
              ⚠️ Exceeds drawer by RM {{ fmtRM(gb.gt.value - MOCK_CASH_BALANCE) }}
            </div>
          </div>
          <div v-if="gb.pm.value === 'custacct'" class="info-box info-blue" style="margin-bottom: 0">
            Posts to Customer AP ledger. Auto-netting JE nets against existing AR balance.
          </div>
          <div v-if="gb.pm.value === 'mix'">
            <table class="mix-tbl">
              <thead><tr><th>Mode</th><th style="text-align: right">Amount (RM)</th><th style="width: 28px"></th></tr></thead>
              <tbody>
                <tr v-for="row in gb.mixRows.value" :key="row.id">
                  <td>
                    <select :value="row.mode" @change="e => gb.updateMixRow(row.id, 'mode', e.target.value)"><option>Cash</option><option>Bank Transfer</option><option>Customer Account</option></select>
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
                    @blur="e => { const v = parseFloat(e.target.value.replace(/,/g,'')); gb.updateMixRow(row.id, 'amount', isNaN(v) ? '' : fmtRM(v)) }"
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
                    <span v-else class="warn-badge">⚠ RM {{ fmtRM(Math.abs(gb.mixDiff.value)) }}</span>
                  </td>
                  <td></td>
                </tr>
              </tbody>
            </table>
            <span class="add-link" @click="gb.addMixRow()">+ Add Payment Method</span>
          </div>
        </div>
      </div>

      <!-- TOTALS -->
      <div class="m-sec">
        <div class="m-sec-hdr" @click="gb.togSec('tots')">
          <div class="m-sec-hl">
            <span class="m-sec-ttl">Totals</span>
            <span v-if="gb.gt.value > 0" class="m-sec-note ok">RM {{ fmtRM(gb.gt.value) }}</span>
          </div>
          <span :class="['m-chev', gb.mSec.value.tots ? 'open' : '']">▶</span>
        </div>
        <div v-if="gb.mSec.value.tots" class="m-sec-body">
          <div class="m-tot-row"><span class="l">Total Gross Wt</span><span class="v">{{ fmtWt(gb.totGross.value) }}</span></div>
          <div class="m-tot-row"><span class="l">Total Net Wt</span><span class="v">{{ fmtWt(gb.totNet.value) }}</span></div>
          <div class="m-tot-row"><span class="l">Total Amount</span><span class="v">RM {{ fmtRM(gb.totAmt.value) }}</span></div>
          <div class="m-tot-row">
            <span class="l" style="display: flex; align-items: center; gap: 6px">
              <input type="checkbox" v-model="gb.round.value" style="accent-color: var(--gold); width: 13px; height: 13px" />
              Rounding
              <span v-if="gb.round.value" style="font-size: 11px; color: var(--text-subtle)">{{ gb.roundHint.value }}</span>
            </span>
            <span class="v" style="color: var(--text-subtle)">{{ gb.round.value ? 'on' : 'off' }}</span>
          </div>
          <div class="m-disc-row">
            <span class="l">Discount (RM)</span>
            <input placeholder="0.00" :value="gb.discDisp.value"
              @focus="e => gb.discDisp.value = e.target.value.replace(/,/g, '')"
              @input="e => { gb.discDisp.value = e.target.value; gb.disc.value = e.target.value }"
              @blur="e => { const v = parseFloat(e.target.value.replace(/,/g, '')); gb.disc.value = isNaN(v) ? '' : String(v); gb.discDisp.value = isNaN(v) ? '' : fmtRM(v) }"
              @keydown.enter="e => e.target.blur()"
            />
          </div>
          <div class="m-grand-row"><span class="l">Grand Total</span><span class="v">RM {{ fmtRM(gb.gt.value) }}</span></div>
        </div>
      </div>

      <!-- SUMMARY -->
      <div class="m-sec">
        <div class="m-sec-hdr" @click="gb.togSec('summ')">
          <div class="m-sec-hl">
            <span class="m-sec-ttl">Summary</span>
            <span v-if="gb.totXAU.value > 0" class="m-sec-note ok">{{ gb.totXAU.value.toFixed(3) }} XAU</span>
          </div>
          <span :class="['m-chev', gb.mSec.value.summ ? 'open' : '']">▶</span>
        </div>
        <div v-if="gb.mSec.value.summ" class="m-sec-body">
          <div class="m-summ-row"><span style="color: var(--text-muted)">Grand Total</span><span style="font-weight: 700; color: var(--gold)">RM {{ fmtRM(gb.gt.value) }}</span></div>
          <div class="m-summ-row"><span style="color: var(--text-muted)">Total XAU</span><span style="font-weight: 600">{{ gb.totXAU.value.toFixed(3) }} XAU</span></div>
          <div class="m-summ-row"><span style="color: var(--text-muted)">XAU AVCO</span><span style="font-weight: 600">{{ gb.totXAU.value > 0 ? `RM ${fmtRM(gb.gt.value / gb.totXAU.value)} / XAU` : '— / XAU' }}</span></div>
        </div>
      </div>

      <!-- GL -->
      <div class="m-sec">
        <div class="m-sec-hdr" @click="gb.togSec('gl')">
          <div class="m-sec-hl"><span class="m-sec-ttl">GL Entries</span><span class="m-sec-note">preview</span></div>
          <span :class="['m-chev', gb.mSec.value.gl ? 'open' : '']">▶</span>
        </div>
        <div v-if="gb.mSec.value.gl" class="m-sec-body">
          <div class="gl-sub" style="margin-bottom: 8px">GL Entries</div>
          <table class="gl" style="font-size: 12px; margin-bottom: 14px">
            <thead><tr><th>Account</th><th class="r">Dr</th><th class="r">Cr</th></tr></thead>
            <tbody>
              <tr v-if="!gb.glRows.value.length"><td colspan="3" style="color: var(--text-subtle); text-align: center; padding: 10px">Fill items to preview</td></tr>
              <tr v-for="(r, i) in gb.glRows.value" :key="i">
                <td>{{ r.acct }}</td><td :class="r.dr !== '—' ? 'dr' : 'dash'">{{ r.dr }}</td><td :class="r.cr !== '—' ? 'cr' : 'dash'">{{ r.cr }}</td>
              </tr>
            </tbody>
          </table>
          <div class="gl-sub" style="margin-bottom: 8px">Stock Entries</div>
          <table class="gl" style="font-size: 12px">
            <thead><tr><th>Item</th><th>Warehouse</th><th class="r">XAU</th><th class="r">Net Wt</th></tr></thead>
            <tbody>
              <tr v-if="!gb.stRows.value.length"><td colspan="4" style="color: var(--text-subtle); text-align: center; padding: 10px">Fill items to preview</td></tr>
              <tr v-for="(r, i) in gb.stRows.value" :key="i">
                <td>{{ r.item }}</td><td style="font-size: 11px">{{ r.wh }}</td><td class="dr">{{ r.xau }}</td><td class="dr">{{ r.nw }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- MODALS (mobile) -->
    <DeductModal v-if="gb.dedModal.value" :item="gb.dedModal.value"
      @close="gb.dedModal.value = null"
      @apply="rows => { gb.applyDeds(gb.dedModal.value.id, rows); gb.dedModal.value = null }" />
    <NewCustModal v-if="gb.showNewCust.value"
      @close="gb.showNewCust.value = false"
      @save="onMobileNewCustSave" />
    <OverageModal v-if="gb.ovgModal.value" :lines="ovgLines"
      @close="gb.ovgModal.value = false"
      @confirm="gb.confirmOvg()" />
  </div>

  <!-- DRAFT VIEW — DESKTOP -->
  <div v-else style="height: 100%; overflow-y: auto">
    <div class="form-page">
      <!-- DOC TOPBAR -->
      <div class="doc-topbar">
        <div class="topbar-left">
          <button class="back-btn">← Gold Buyback</button>
          <span class="doc-title">New Purchase Receipt</span>
          <span :class="['status-badge', `status-${gb.status.value}`]">
            {{ gb.status.value === 'draft' ? 'Not Saved' : 'Saved' }}
          </span>
        </div>
        <div class="topbar-right-btns">
          <button class="btn btn-primary" @click="gb.goReview()">Save Draft</button>
        </div>
      </div>

      <!-- VALIDATION ERRORS -->
      <div v-if="gb.validationErrors.value.length"
        style="background: var(--red-light); border: 1px solid var(--red-border); border-radius: var(--radius); padding: 12px 16px; margin-bottom: 0; margin-top: 0">
        <div v-for="(e, i) in gb.validationErrors.value" :key="i"
          style="font-size: 12px; color: var(--red); display: flex; align-items: center; gap: 6px"
          :style="{ marginBottom: i < gb.validationErrors.value.length - 1 ? '4px' : 0 }">
          <span style="font-weight: 700">⚠</span>{{ e }}
        </div>
      </div>

      <!-- PURCHASE TYPE -->
      <div class="purchase-type-bar">
        <span class="pt-label">Purchase Type</span>
        <div class="toggle-wrap">
          <span :class="['toggle-label', !gb.niH.value ? 'active' : '']">Item in Hand</span>
          <label class="toggle-switch">
            <input type="checkbox" :checked="gb.niH.value" @change="e => gb.niH.value = e.target.checked" />
            <span class="toggle-track"></span>
          </label>
          <span :class="['toggle-label', gb.niH.value ? 'active' : '']">Item Not In Hand</span>
        </div>
      </div>

      <!-- META CARD -->
      <div class="card">
        <div class="card-body">
          <div class="grid-3" style="gap: 16px; margin-bottom: 14px">
            <div class="field"><label>Series / Document No.</label><div class="series-display">{{ gb.docNo.value }}</div></div>
            <div class="field"><label>Date <span class="req">*</span></label>
              <input type="date" class="field-input" :value="today" :disabled="!gb.editTime.value" />
            </div>
            <div class="field"><label>Company</label><div class="series-display">Anygold Sdn. Bhd.</div></div>
          </div>
          <div style="display: flex; align-items: center; gap: 20px">
            <div class="field" style="width: 200px">
              <label>Posting Time <span class="req">*</span></label>
              <input type="time" class="field-input" :value="gb.time.value" :disabled="!gb.editTime.value"
                @change="e => gb.time.value = e.target.value" />
            </div>
            <label style="display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text-muted); cursor: pointer; margin-top: 18px">
              <input type="checkbox" :checked="gb.editTime.value" @change="e => gb.editTime.value = e.target.checked"
                style="accent-color: var(--gold); width: 14px; height: 14px" />
              Edit Posting Date &amp; Time
            </label>
          </div>
        </div>
      </div>

      <!-- CUSTOMER + PAYMENT (one combined card, two-col layout) -->
      <CustomerSection />

      <!-- RATE LOCKS (dealer only) -->
      <RateLockSection />

      <!-- BAG BAR -->
      <BagBar />

      <!-- ITEMS TABLE -->
      <ItemsTable />

      <!-- SUMMARY -->
      <SummarySection />

      <!-- GL ENTRIES -->
      <GlEntriesSection />
    </div>

    <!-- MODALS (desktop) -->
    <!-- NewCustModal is handled inside CustomerSection.vue via <teleport> for desktop. -->
    <DeductModal v-if="gb.dedModal.value" :item="gb.dedModal.value"
      @close="gb.dedModal.value = null"
      @apply="rows => { gb.applyDeds(gb.dedModal.value.id, rows); gb.dedModal.value = null }" />
    <OverageModal v-if="gb.ovgModal.value" :lines="ovgLines"
      @close="gb.ovgModal.value = false"
      @confirm="gb.confirmOvg()" />
  </div>
</template>

<script setup>
import { computed, provide } from 'vue'
import { useGoldBuyback } from '../../composables/useGoldBuyback.js'
import { fmtRM, fmtWt, fmtMobileStr } from '../../utils/formatters.js'
import { BAG_OPTIONS, PM_LABELS, MOCK_CASH_BALANCE } from '../../constants/index.js'

// ── SHARED COMPOSABLE ──
// All state and methods live here. Provided to ALL child components via inject('gb').
// Children never receive props for business logic — they inject 'gb' directly.
const gb = useGoldBuyback()
provide('gb', gb)

// ── CHILD COMPONENT IMPORTS ──
import CustomerSection  from './components/CustomerSection.vue'
import BagBar           from './components/BagBar.vue'
import RateLockSection  from './components/RateLockSection.vue'
import ItemsTable       from './components/ItemsTable.vue'
import SummarySection   from './components/SummarySection.vue'
import GlEntriesSection from './components/GlEntriesSection.vue'
import MobileItemCard   from './components/MobileItemCard.vue'
import DeductModal      from './modals/DeductModal.vue'
import NewCustModal     from './modals/NewCustModal.vue'
import OverageModal     from './modals/OverageModal.vue'
import ReviewPage       from './views/ReviewPage.vue'
import SubmittedPage    from './views/SubmittedPage.vue'

const today = computed(() => new Date().toISOString().slice(0, 10))

// Mobile new-customer save handler — receives the full custObj emitted by NewCustModal.
const onMobileNewCustSave = (custObj) => {
  gb.cust.value             = custObj
  gb.search.value           = custObj.name
  gb.showDD.value           = false
  gb.showNewCust.value      = false
  gb.locks.value            = []
  gb.validationErrors.value = []
}

// Mobile balance display
const mobileBalanceDisplay = computed(() => {
  if (gb.custAcctAmt.value > 0) {
    const pb = (gb.cust.value?.advance || 0) - gb.custAcctAmt.value
    return `RM ${fmtRM(Math.abs(pb))} ${pb >= 0 ? '(they owe us)' : '(we owe them)'}`
  }
  const adv = gb.cust.value?.advance || 0
  return `RM ${fmtRM(Math.abs(adv))} ${adv > 0 ? 'AR' : adv < 0 ? 'AP' : ''}`
})

// Overage summary for modal
const ovgLines = computed(() =>
  gb.unresolved.value.map(item => {
    const rem = gb.getLockRem(item.lockId, item.id)
    const excess = (item.net || item.gross || 0) - rem
    return `• ${item.desc || 'Item'} (${item.purity}): exceeds ${item.lockId} by ${excess.toFixed(3)}g`
  }).join('\n')
)
</script>


