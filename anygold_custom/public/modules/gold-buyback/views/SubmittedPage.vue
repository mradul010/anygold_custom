<template>
  <!-- MOBILE -->
  <div v-if="gb.isMobile.value" style="height: 100%; overflow-y: auto; background: var(--bg)">
    <div class="m-doc-hdr">
      <div class="m-hdr-r1">
        <button class="m-back">← Buyback</button>
        <div style="display: flex; align-items: center; gap: 6px">
          <span class="m-doc-title">{{ gb.docNo.value }}</span>
          <span class="status-badge status-submitted">Submitted</span>
        </div>
        <button class="btn btn-green" style="padding: 6px 12px; font-size: 12px" @click="gb.newPurchase()">＋ New</button>
      </div>
      <div style="display: flex; gap: 6px; margin-top: 8px">
        <button class="btn btn-outline" style="flex: 1; font-size: 12px; padding: 6px 8px" @click="alert('Print A5')">🖨 A5</button>
        <button class="btn btn-outline" style="flex: 1; font-size: 12px; padding: 6px 8px" @click="alert('Print Thermal')">🖨 Thermal</button>
        <button class="btn btn-outline" style="flex: 1; font-size: 12px; padding: 6px 8px">≡ List</button>
      </div>
    </div>
    <div class="m-scroll">
      <div style="background: var(--green-light); border: 1px solid #86EFAC; border-radius: var(--radius); padding: 14px 16px; display: flex; align-items: center; gap: 12px">
        <span style="font-size: 28px">✅</span>
        <div>
          <div style="font-size: 14px; font-weight: 700; color: var(--green)">Submitted Successfully</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px">
            <span style="font-weight: 700; color: var(--text)">{{ gb.docNo.value }}</span> · {{ dateStr }} · {{ timeStr }}
          </div>
        </div>
      </div>
      <!-- Customer -->
      <div class="m-sec">
        <div class="m-sec-hdr"><div class="m-sec-hl"><span class="m-sec-ttl">Customer</span></div></div>
        <div class="m-sec-body">
          <div style="font-size: 14px; font-weight: 700; margin-bottom: 4px">{{ gb.cust.value?.name || '—' }}</div>
          <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 2px">IC: {{ gb.cust.value?.ic || '—' }}</div>
          <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 8px">📱 {{ gb.cust.value ? fmtMobileStr(gb.cust.value.mobile) : '—' }}</div>
          <div style="display: flex; gap: 6px; flex-wrap: wrap">
            <span style="font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 10px; background: var(--blue-light); color: var(--blue)">{{ gb.cust.value?.type || '—' }}</span>
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
              <div><div style="color: var(--text-subtle); font-size: 10px; text-transform: uppercase; letter-spacing: 0.04em">Net Wt</div><div style="font-weight: 600" :style="{ color: dedNoteText(item.deds) ? 'var(--gold)' : 'inherit' }">{{ fmtWt(item.net || 0) }}</div></div>
              <div><div style="color: var(--text-subtle); font-size: 10px; text-transform: uppercase; letter-spacing: 0.04em">Rate</div><div style="font-weight: 600">RM {{ fmtRM(item.rate || 0) }}</div></div>
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
            <div class="m-tot-row"><span class="l">Total XAU</span><span class="v">{{ gb.totXAU.value.toFixed(3) }} XAU</span></div>
            <div class="m-tot-row"><span class="l">XAU AVCO</span><span class="v">{{ gb.totXAU.value > 0 ? `RM ${fmtRM(gb.gt.value / gb.totXAU.value)}/XAU` : '—' }}</span></div>
            <div class="m-grand-row"><span class="l">Grand Total</span><span class="v">RM {{ fmtRM(gb.gt.value) }}</span></div>
          </div>
        </div>
      </div>
      <!-- Payment -->
      <div class="m-sec">
        <div class="m-sec-hdr"><div class="m-sec-hl"><span class="m-sec-ttl">Payment</span></div></div>
        <div class="m-sec-body">
          <div v-if="gb.summPay.value.length" v-for="(r, i) in gb.summPay.value" :key="i" class="m-summ-row">
            <span style="color: var(--text-muted)">{{ r.label }}</span><span style="font-weight: 600">RM {{ r.val }}</span>
          </div>
          <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 10px; margin-top: 4px; border-top: 2px solid var(--border-strong)">
            <span style="font-size: 13px; font-weight: 700">Grand Total</span>
            <span style="font-size: 18px; font-weight: 700; color: var(--gold)">RM {{ fmtRM(gb.gt.value) }}</span>
          </div>
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
          <span class="status-badge status-submitted">Submitted</span>
        </div>
        <div class="topbar-right-btns">
          <button class="btn btn-outline" @click="alert('Print A5')">🖨 A5</button>
          <button class="btn btn-outline" @click="alert('Print Thermal')">🖨 Thermal</button>
          <button class="btn btn-outline">≡ Purchase List</button>
          <button class="btn btn-green" @click="gb.newPurchase()">＋ New Purchase</button>
        </div>
      </div>

      <!-- SUCCESS BANNER -->
      <div style="background: var(--green-light); border: 1px solid #86EFAC; border-radius: var(--radius); padding: 16px 20px; margin-bottom: 12px; display: flex; align-items: center; gap: 14px">
        <div style="font-size: 32px; line-height: 1">✅</div>
        <div>
          <div style="font-size: 15px; font-weight: 700; color: var(--green)">Purchase Submitted Successfully</div>
          <div style="font-size: 12px; color: var(--text-muted); margin-top: 2px">
            <span style="font-weight: 600; color: var(--text)">{{ gb.docNo.value }}</span>
            · {{ dateStr }} · {{ timeStr }}
          </div>
        </div>
      </div>

      <!-- CUSTOMER + PAYMENT SIDE BY SIDE -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px">
        <div class="card" style="margin-bottom: 0">
          <div class="card-header">Customer</div>
          <div class="card-body">
            <div style="font-size: 15px; font-weight: 700; margin-bottom: 6px">{{ gb.cust.value?.name || '—' }}</div>
            <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 2px">IC: {{ gb.cust.value?.ic || '—' }}</div>
            <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 8px">Mobile: {{ gb.cust.value ? fmtMobileStr(gb.cust.value.mobile) : '—' }}</div>
            <span style="font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 10px; background: var(--blue-light); color: var(--blue)">{{ gb.cust.value?.type || '—' }}</span>
          </div>
        </div>
        <div class="card" style="margin-bottom: 0">
          <div class="card-header">Payment</div>
          <div class="card-body">
            <div v-for="(r, i) in gb.summPay.value" :key="i" class="summ-row">
              <span class="lbl">{{ r.label }}</span><span class="val">RM {{ r.val }}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 10px; margin-top: 6px; border-top: 2px solid var(--border-strong)">
              <span style="font-size: 13px; font-weight: 700">Grand Total</span>
              <span style="font-size: 16px; font-weight: 700; color: var(--gold)">RM {{ fmtRM(gb.gt.value) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ITEMS -->
      <div class="card">
        <div class="card-header">Items Purchased</div>
        <div class="items-wrap">
          <table style="width: 100%; border-collapse: collapse; table-layout: fixed">
            <colgroup>
              <col style="width: 36px" /><col /><col style="width: 72px" />
              <col style="width: 108px" /><col style="width: 120px" /><col style="width: 130px" />
            </colgroup>
            <thead>
              <tr style="border-bottom: 2px solid var(--border)">
                <th style="padding: 8px 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-subtle)">#</th>
                <th style="padding: 8px 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-subtle)">Description</th>
                <th style="padding: 8px 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-subtle); text-align: center">Purity</th>
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
                  <td style="padding: 10px 12px; font-size: 13px; text-align: right" :style="{ color: dedNoteText(item.deds) ? 'var(--gold)' : 'inherit', fontWeight: dedNoteText(item.deds) ? 600 : 400 }">{{ fmtWt(item.net || 0) }}</td>
                  <td style="padding: 10px 12px; font-size: 13px; text-align: right">RM {{ fmtRM(item.rate || 0) }}</td>
                  <td style="padding: 10px 20px 10px 12px; font-size: 13px; text-align: right; font-weight: 500">RM {{ fmtRM(item.amount || 0) }}</td>
                </tr>
                <tr v-if="dedNoteText(item.deds)" style="border-bottom: 1px solid var(--border)">
                  <td></td><td colspan="5" style="padding: 2px 12px 10px; font-size: 11px; color: var(--text-muted)">↳ Deductions: {{ dedNoteText(item.deds) }}</td>
                </tr>
                <tr v-if="item.bag && item.bag !== gb.defBag.value" style="border-bottom: 1px solid var(--border)">
                  <td></td><td colspan="5" style="padding: 2px 12px 10px; font-size: 11px; color: var(--text-muted)">↳ Bag: {{ item.bag }}</td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
        <div class="totals-section">
          <div class="totals-inner"><div class="totals-right-block">
            <div class="tot-row"><span class="lbl">Total Gross Weight</span><span class="val">{{ fmtWt(gb.totGross.value) }}</span></div>
            <div class="tot-row"><span class="lbl">Total Net Weight</span><span class="val">{{ fmtWt(gb.totNet.value) }}</span></div>
            <div class="tot-divider"></div>
            <div class="tot-row"><span class="lbl">Total XAU</span><span class="val">{{ gb.totXAU.value.toFixed(3) }} XAU</span></div>
            <div class="tot-row"><span class="lbl">XAU AVCO</span><span class="val">{{ gb.totXAU.value > 0 ? `RM ${fmtRM(gb.gt.value / gb.totXAU.value)} / XAU` : '— / XAU' }}</span></div>
            <div class="tot-divider"></div>
            <div class="grand-row"><span class="lbl">Grand Total</span><span class="val">RM {{ fmtRM(gb.gt.value) }}</span></div>
          </div></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, inject } from 'vue'
import { fmtRM, fmtWt, fmtMobileStr, dedNoteText } from '../../../utils/formatters.js'
const gb = inject('gb')
const now = new Date()
const dateStr = computed(() => now.toLocaleDateString('en-MY', { day: '2-digit', month: 'short', year: 'numeric' }))
const timeStr = computed(() => now.toLocaleTimeString('en-MY', { hour: '2-digit', minute: '2-digit', second: '2-digit' }))
</script>

