<template>
  <div class="card">
    <div class="card-body">
      <div class="summary-inner">
        <!-- PAYMENT BREAKDOWN -->
        <div>
          <div class="summ-sub">Payment Breakdown</div>
          <div v-for="(r, i) in gb.summPay.value" :key="i" class="summ-row">
            <span class="lbl">{{ r.label }}</span>
            <span class="val">RM {{ r.val }}</span>
          </div>
          <div v-if="!gb.summPay.value.length" class="summ-row">
            <span class="lbl" style="color: var(--text-subtle)">No payment method selected</span>
          </div>
        </div>
        <!-- DIVIDER -->
        <div class="summ-sep"><div class="summ-sep-line"></div></div>
        <!-- TRANSACTION SUMMARY -->
        <div>
          <div class="summ-sub">Transaction Summary</div>
          <div class="summ-row">
            <span class="lbl">Grand Total</span>
            <span class="val gold">RM {{ fmtRM(gb.gt.value) }}</span>
          </div>
          <div class="summ-row">
            <span class="lbl">Total XAU</span>
            <span class="val">{{ gb.totXAU.value.toFixed(3) }} XAU</span>
          </div>
          <div class="summ-row">
            <span class="lbl">XAU AVCO</span>
            <span class="val">
              {{ gb.totXAU.value > 0 ? `RM ${fmtRM(gb.gt.value / gb.totXAU.value)} / XAU` : '— / XAU' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue'
import { fmtRM } from '../../../utils/formatters.js'
const gb = inject('gb')
</script>
