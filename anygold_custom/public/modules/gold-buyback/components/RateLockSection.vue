<template>
  <!-- Only shown for Dealer customers with locks — exact match to original -->
  <div v-if="gb.custIsDealer.value && gb.locks.value.length > 0" class="lock-section">
    <div class="lock-toggle" @click="gb.lockOpen.value = !gb.lockOpen.value">
      <div class="lock-toggle-left">
        <span>🔒</span>
        <span class="lock-toggle-title">Rate Locks</span>
        <span class="lock-badge">{{ activeCount }} Active</span>
      </div>
      <span :class="['lock-chev', gb.lockOpen.value ? 'open' : '']">▶</span>
    </div>
    <div :class="['lock-body', gb.lockOpen.value ? 'open' : '']">
      <table class="lock-tbl">
        <thead>
          <tr>
            <th>#</th>
            <th>Lock ID</th>
            <th>Locked On</th>
            <th>Purity</th>
            <th>Locked Rate</th>
            <th>Locked (g)</th>
            <th>Remaining (g)</th>
            <th>Status</th>
            <th>In Use</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(lk, i) in gb.locks.value" :key="lk.id">
            <td class="row-num">{{ i + 1 }}</td>
            <td class="lock-id">{{ lk.id }}</td>
            <td style="color: var(--text-muted); font-size: 12px">{{ lk.time }}</td>
            <td>{{ lk.purity }}</td>
            <td>RM {{ fmtRM(lk.rate) }}/g</td>
            <td>{{ lk.originalWt.toFixed(3) }} g</td>
            <td :class="['lock-rem', remClass(lk)]">{{ rem(lk).toFixed(3) }} g</td>
            <td>
              <span v-if="Math.abs(rem(lk)) < 0.0005" class="lock-status used">✅ Fully Used</span>
              <span v-else-if="rem(lk) < -0.0005" class="lock-status over-by">🟠 Over by {{ Math.abs(rem(lk)).toFixed(3) }}g</span>
              <span v-else-if="lk.status === 'Active'"   class="lock-status active">🟢 Active</span>
              <span v-else-if="lk.status === 'Expiring'" class="lock-status expiring">🟡 Expiring</span>
              <span v-else class="lock-status overdue">🟠 Overdue</span>
            </td>
            <td>
              <span v-if="inUse(lk.id)" class="in-use-pill">In Use</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, inject } from 'vue'
import { fmtRM } from '../../../utils/formatters.js'

const gb = inject('gb')

const activeCount = computed(() =>
  gb.locks.value.filter(l => ['Active', 'Expiring', 'Overdue'].includes(l.status)).length
)

const rem = (lk) => {
  const used = gb.items.value.reduce((s, it) =>
    it.lockId === lk.id ? s + (it.net || it.gross || 0) : s, 0
  )
  return lk.originalWt - used
}

const remClass = (lk) => {
  const r = rem(lk)
  if (Math.abs(r) < 0.0005) return 'zero'
  if (r < -0.0005) return 'over'
  return 'positive'
}

const inUse = (lockId) => gb.items.value.some(it => it.lockId === lockId)
</script>
