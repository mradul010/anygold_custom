<template>
  <div class="gl-section">
    <div class="gl-toggle" @click="gb.glOpen.value = !gb.glOpen.value">
      <span :class="['gl-chev', gb.glOpen.value ? 'open' : '']">▶</span>
      Accounting &amp; Stock Entries
      <span style="margin-left: 6px; font-size: 10px; color: var(--text-subtle); font-weight: 400; text-transform: none; letter-spacing: 0">(preview — posts on Submit)</span>
    </div>
    <div v-if="gb.glOpen.value" class="gl-body">
      <!-- GL ENTRIES -->
      <div class="gl-sub">GL Entries</div>
      <table class="gl">
        <thead>
          <tr>
            <th>Account</th>
            <th class="r">Debit (RM)</th>
            <th class="r">Credit (RM)</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="gb.glRows.value.length">
            <tr v-for="(r, i) in gb.glRows.value" :key="i">
              <td>{{ r.acct }}</td>
              <td :class="r.dr !== '—' ? 'dr' : 'dash'">{{ r.dr }}</td>
              <td :class="r.cr !== '—' ? 'cr' : 'dash'">{{ r.cr }}</td>
            </tr>
          </template>
          <tr v-else>
            <td colspan="3" style="color: var(--text-subtle); text-align: center; padding: 14px">
              Fill in items to preview
            </td>
          </tr>
        </tbody>
      </table>

      <!-- STOCK ENTRIES -->
      <!-- Stores both gross_weight AND net_weight per item per purity per warehouse
           gross_weight → physical bag stock tally (staff weighs purity groups on scale)
           net_weight   → accounting, XAU, AVCO calculations -->
      <div class="gl-sub">Stock Entries</div>
      <table class="gl">
        <thead>
          <tr>
            <th>Item</th>
            <th>Warehouse (Bag)</th>
            <th class="r">XAU</th>
            <th class="r">Net Wt</th>
            <th class="r">Gross Wt</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="gb.stRows.value.length">
            <tr v-for="(r, i) in gb.stRows.value" :key="i">
              <td>{{ r.item }}</td>
              <td style="font-size: 12px">{{ r.wh }}</td>
              <td class="dr">{{ r.xau }}</td>
              <td class="dr">{{ r.nw }}</td>
              <td class="dr">{{ r.gw }}</td>
            </tr>
          </template>
          <tr v-else>
            <td colspan="5" style="color: var(--text-subtle); text-align: center; padding: 14px">
              Fill in items to preview
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue'
const gb = inject('gb')
</script>
