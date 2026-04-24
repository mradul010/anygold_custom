<template>
  <!-- MOBILE -->
  <div v-if="gb.isMobile.value" style="height: 100%; overflow-y: auto; background: var(--bg)">
    <div class="m-doc-hdr">
      <div class="m-hdr-r1">
        <button class="m-back">← Buyback</button>
        <div style="display: flex; align-items: center; gap: 6px">
          <span class="m-doc-title">{{ gb.docNo.value }}</span>
          <span class="status-badge status-saved">Saved</span>
        </div>
        <div style="display: flex; gap: 6px">
          <button class="btn btn-outline" style="padding: 6px 12px; font-size: 12px" @click="gb.view.value = 'draft'">Edit</button>
          <button class="btn btn-gold" style="padding: 6px 12px; font-size: 12px" @click="gb.goSubmit()">Submit</button>
        </div>
      </div>
    </div>
    <div class="m-scroll">
      <div style="background: var(--gold-light); border: 1px solid var(--gold-border); border-radius: var(--radius); padding: 12px 14px; display: flex; align-items: center; gap: 10px">
        <span style="font-size: 20px">📋</span>
        <div>
          <div style="font-size: 13px; font-weight: 700; color: var(--gold)">Review Before Submitting</div>
          <div style="font-size: 11px; color: var(--text-muted)">Press Edit to make changes.</div>
        </div>
      </div>
      <!-- Transaction -->
      <div class="m-sec">
        <div class="m-sec-hdr"><div class="m-sec-hl"><span class="m-sec-ttl">Transaction</span></div></div>
        <div class="m-sec-body">
          <div class="m-g2">
            <div class="m-f"><label>Document</label><div class="m-ro">{{ gb.docNo.value }}</div></div>
            <div class="m-f"><label>Date</label><div class="m-ro">{{ today }}</div></div>
          </div>
          <div class="m-g2">
            <div class="m-f"><label>Purchase Type</label><div class="m-ro">{{ gb.niH.value ? 'Not In Hand' : 'In Hand' }}</div></div>
            <div class="m-f"><label>Default Bag</label><div class="m-ro" style="font-size: 12px">{{ gb.defBag.value }}</div></div>
          </div>
        </div>
      </div>
      <!-- Customer + Payment -->
      <div class="m-sec">
        <div class="m-sec-hdr"><div class="m-sec-hl"><span class="m-sec-ttl">Customer &amp; Payment</span></div></div>
        <div class="m-sec-body">
          <div class="m-g2">
            <div class="m-f"><label>Customer</label><div class="m-ro" style="font-size: 12px">{{ gb.cust.value?.name || '—' }}</div></div>
            <div class="m-f"><label>IC</label><div class="m-ro">{{ gb.cust.value?.ic || '—' }}</div></div>
          </div>
          <div class="m-g2">
            <div class="m-f"><label>Mobile</label><div class="m-ro">{{ gb.cust.value ? fmtMobileStr(gb.cust.value.mobile) : '—' }}</div></div>
            <div class="m-f"><label>Payment</label><div class="m-ro">{{ PM_LABELS[gb.pm.value] || '—' }}</div></div>
          </div>
        </div>
      </div>
      <!-- Items -->
      <div class="m-sec">
        <div class="m-sec-hdr"><div class="m-sec-hl"><span class="m-sec-ttl">Items</span></div></div>
        <div class="m-sec-body" style="padding: 10px">
          <div v-for="(item, i) in gb.items.value" :key="item.id"
            style="border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 10px 12px; margin-bottom: 8px; background: var(--surface)">
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px">
              <span style="font-size: 12px; font-weight: 700; color: var(--text-muted)">{{ i + 1 }}. {{ item.desc || '—' }}</span>
              <span style="font-size: 12px; font-weight: 700">{{ item.purity }}</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; font-size: 12px">
              <div><div style="color: var(--text-subtle); font-size: 10px; text-transform: uppercase; letter-spacing: 0.04em">Gross</div><div style="font-weight: 600">{{ fmtWt(item.gross || 0) }}</div></div>
              <div><div style="color: var(--text-subtle); font-size: 10px; text-transform: uppercase; letter-spacing: 0.04em">Net</div><div :style="{ fontWeight: 600, color: dedNoteText(item.deds) ? 'var(--gold)' : 'inherit' }">{{ fmtWt(item.net || 0) }}</div></div>
              <div><div style="color: var(--text-subtle); font-size: 10px; text-transform: uppercase; letter-spacing: 0.04em">Amount</div><div style="font-weight: 600">RM {{ fmtRM(item.amount || 0) }}</div></div>
            </div>
            <div v-if="dedNoteText(item.deds) || (item.bag && item.bag !== gb.defBag.value)"
              style="margin-top: 6px; padding-top: 6px; border-top: 1px solid var(--border); font-size: 11px; color: var(--text-muted); display: flex; flex-direction: column; gap: 2px">
              <span v-if="dedNoteText(item.deds)">↳ Ded: {{ dedNoteText(item.deds) }}</span>
              <span v-if="item.bag && item.bag !== gb.defBag.value">↳ Bag: {{ item.bag }}</span>
            </div>
          </div>
          <div style="padding: 10px 4px">
            <div class="m-tot-row"><span class="l">Total Gross Wt</span><span class="v">{{ fmtWt(gb.totGross.value) }}</span></div>
            <div class="m-tot-row"><span class="l">Total Net Wt</span><span class="v">{{ fmtWt(gb.totNet.value) }}</span></div>
            <div class="m-tot-row"><span class="l">Total Amount</span><span class="v">RM {{ fmtRM(gb.totAmt.value) }}</span></div>
            <div class="m-grand-row"><span class="l">Grand Total</span><span class="v">RM {{ fmtRM(gb.gt.value) }}</span></div>
          </div>
        </div>
      </div>
      <!-- Summary -->
      <div class="m-sec">
        <div class="m-sec-hdr"><div class="m-sec-hl"><span class="m-sec-ttl">Summary</span></div></div>
        <div class="m-sec-body">
          <div class="m-summ-row"><span style="color: var(--text-muted)">Grand Total</span><span style="font-weight: 700; color: var(--gold)">RM {{ fmtRM(gb.gt.value) }}</span></div>
          <div class="m-summ-row"><span style="color: var(--text-muted)">Total XAU</span><span style="font-weight: 600">{{ gb.totXAU.value.toFixed(3) }} XAU</span></div>
          <div class="m-summ-row"><span style="color: var(--text-muted)">XAU AVCO</span><span style="font-weight: 600">{{ gb.totXAU.value > 0 ? `RM ${fmtRM(gb.gt.value / gb.totXAU.value)} / XAU` : '— / XAU' }}</span></div>
        </div>
      </div>
    </div>
  </div>

  <!-- DESKTOP -->
  <div v-else style="height: 100%; overflow-y: auto">
    <div class="form-page">
      <div class="doc-topbar">
        <div class="topbar-left">
          <button class="back-btn">← Gold Buyback</button>
          <span class="doc-title">{{ gb.docNo.value }}</span>
          <span class="status-badge status-saved">Saved</span>
        </div>
        <div class="topbar-right-btns">
          <button class="btn btn-outline" @click="gb.view.value = 'draft'">Edit</button>
          <button class="btn btn-gold" @click="gb.goSubmit()">Submit</button>
        </div>
      </div>

      <!-- REVIEW NOTICE -->
      <div class="card" style="border-color: var(--gold-border); background: var(--gold-light)">
        <div class="card-body" style="display: flex; align-items: center; justify-content: space-between">
          <div>
            <div style="font-size: 14px; font-weight: 700; color: var(--gold); margin-bottom: 2px">Review Before Submitting</div>
            <div style="font-size: 12px; color: var(--text-muted)">All fields are locked. Press Edit to make changes.</div>
          </div>
          <div style="font-size: 28px">📋</div>
        </div>
      </div>

      <!-- TRANSACTION DETAILS -->
      <div class="card">
        <div class="card-header">Transaction Details</div>
        <div class="card-body">
          <div class="review-grid">
            <div class="review-field"><span class="lbl">Document</span><span class="val">{{ gb.docNo.value }}</span></div>
            <div class="review-field"><span class="lbl">Date &amp; Time</span><span class="val">{{ today }} · {{ gb.time.value }}</span></div>
            <div class="review-field"><span class="lbl">Purchase Type</span><span class="val">{{ gb.niH.value ? 'Item Not In Hand' : 'Item in Hand' }}</span></div>
            <div class="review-field" style="grid-column: 1 / -1">
              <span class="lbl">Bag Destination</span>
              <div style="display: flex; flex-direction: column; gap: 3px; margin-top: 2px">
                <div v-for="(b, i) in gb.bagSummary.value" :key="i" style="font-size: 13px">
                  <span style="font-weight: 500">{{ b.label }}</span>
                  <span v-if="b.note" style="font-size: 11px; color: var(--text-muted); margin-left: 6px">({{ b.note }})</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- CUSTOMER + PAYMENT -->
      <div class="card">
        <div class="card-header">Customer &amp; Payment</div>
        <div class="card-body">
          <div class="review-grid">
            <div class="review-field"><span class="lbl">Customer</span><span class="val">{{ gb.cust.value?.name || '—' }}</span></div>
            <div class="review-field"><span class="lbl">IC Number</span><span class="val">{{ gb.cust.value?.ic || '—' }}</span></div>
            <div class="review-field"><span class="lbl">Mobile</span><span class="val">{{ gb.cust.value ? fmtMobileStr(gb.cust.value.mobile) : '—' }}</span></div>
            <div class="review-field"><span class="lbl">Payment Method</span><span class="val">{{ PM_LABELS[gb.pm.value] || '—' }}</span></div>
          </div>
        </div>
      </div>

      <!-- ITEMS -->
      <div class="card">
        <div class="card-header">Items</div>
        <div class="items-wrap">
          <table style="width: 100%; border-collapse: collapse; table-layout: fixed">
            <colgroup>
              <col style="width: 36px" /><col /><col style="width: 72px" />
              <col style="width: 108px" /><col style="width: 108px" />
              <col style="width: 120px" /><col style="width: 130px" />
            </colgroup>
            <thead>
              <tr style="border-bottom: 2px solid var(--border)">
                <th style="padding: 8px 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-subtle)">#</th>
                <th style="padding: 8px 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-subtle)">Description</th>
                <th style="padding: 8px 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-subtle); text-align: center">Purity</th>
                <th style="padding: 8px 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-subtle); text-align: right">Gross Wt</th>
                <th style="padding: 8px 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-subtle); text-align: right">Net Wt</th>
                <th style="padding: 8px 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-subtle); text-align: right">Rate (RM/g)</th>
                <th style="padding: 8px 20px 8px 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-subtle); text-align: right">Amount (RM)</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="(item, i) in gb.items.value" :key="item.id">
                <tr style="border-bottom: 1px solid var(--border)">
                  <td style="padding: 10px 12px; font-size: 12px; color: var(--text-subtle)">{{ i + 1 }}</td>
                  <td style="padding: 10px 12px; font-size: 13px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">{{ item.desc || '—' }}</td>
                  <td style="padding: 10px 12px; font-size: 13px; text-align: center">{{ item.purity }}</td>
                  <td style="padding: 10px 12px; font-size: 13px; text-align: right">{{ fmtWt(item.gross || 0) }}</td>
                  <td style="padding: 10px 12px; font-size: 13px; text-align: right" :style="{ color: dedNoteText(item.deds) ? 'var(--gold)' : 'inherit', fontWeight: dedNoteText(item.deds) ? 600 : 400 }">{{ fmtWt(item.net || 0) }}</td>
                  <td style="padding: 10px 12px; font-size: 13px; text-align: right">RM {{ fmtRM(item.rate || 0) }}</td>
                  <td style="padding: 10px 20px 10px 12px; font-size: 13px; text-align: right; font-weight: 500">RM {{ fmtRM(item.amount || 0) }}</td>
                </tr>
                <tr v-if="dedNoteText(item.deds)" style="border-bottom: 1px solid var(--border)">
                  <td></td>
                  <td colspan="6" style="padding: 2px 12px 10px; font-size: 11px; color: var(--text-muted)">↳ Deductions: {{ dedNoteText(item.deds) }}</td>
                </tr>
                <tr v-if="gb.showBag.value && item.bag && item.bag !== gb.defBag.value" style="border-bottom: 1px solid var(--border)">
                  <td></td>
                  <td colspan="6" style="padding: 2px 12px 10px; font-size: 11px; color: var(--text-muted)">↳ Bag: {{ item.bag }}</td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
        <div class="totals-section">
          <div class="totals-inner"><div class="totals-right-block">
            <div class="tot-row"><span class="lbl">Total Gross Weight</span><span class="val">{{ fmtWt(gb.totGross.value) }}</span></div>
            <div class="tot-row"><span class="lbl">Total Net Weight</span><span class="val">{{ fmtWt(gb.totNet.value) }}</span></div>
            <div class="tot-row"><span class="lbl">Total Amount</span><span class="val">RM {{ fmtRM(gb.totAmt.value) }}</span></div>
            <div class="tot-divider"></div>
            <div class="grand-row"><span class="lbl">Grand Total</span><span class="val">RM {{ fmtRM(gb.gt.value) }}</span></div>
          </div></div>
        </div>
      </div>

      <!-- SUMMARY -->
      <div class="card">
        <div class="card-body">
          <div class="summary-inner">
            <div>
              <div class="summ-sub">Payment Breakdown</div>
              <div v-for="(r, i) in gb.summPay.value" :key="i" class="summ-row">
                <span class="lbl">{{ r.label }}</span><span class="val">RM {{ r.val }}</span>
              </div>
            </div>
            <div class="summ-sep"><div class="summ-sep-line"></div></div>
            <div>
              <div class="summ-sub">Transaction Summary</div>
              <div class="summ-row"><span class="lbl">Grand Total</span><span class="val gold">RM {{ fmtRM(gb.gt.value) }}</span></div>
              <div class="summ-row"><span class="lbl">Total XAU</span><span class="val">{{ gb.totXAU.value.toFixed(3) }} XAU</span></div>
              <div class="summ-row"><span class="lbl">XAU AVCO</span><span class="val">{{ gb.totXAU.value > 0 ? `RM ${fmtRM(gb.gt.value / gb.totXAU.value)} / XAU` : '— / XAU' }}</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, inject } from 'vue'
import { fmtRM, fmtWt, fmtMobileStr, dedNoteText } from '../../../utils/formatters.js'
import { PM_LABELS } from '../../../constants/index.js'
const gb = inject('gb')
const today = computed(() => new Date().toLocaleDateString('en-MY'))
</script>

