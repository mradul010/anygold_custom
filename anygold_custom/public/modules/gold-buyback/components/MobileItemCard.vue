<template>
  <div class="m-icard">
    <div class="m-icard-hdr">
      <span class="m-icard-num">Item {{ idx + 1 }}</span>
      <button class="m-icard-x" @click="gb.removeItem(item.id)">✕</button>
    </div>

    <!-- DESCRIPTION -->
    <div class="m-if">
      <label>Description</label>
      <input
        ref="descRef"
        type="text"
        style="text-transform: uppercase"
        placeholder="e.g. CINCIN, MIX GOLD..."
        :value="item.desc"
        @input="e => gb.updItem(item.id, 'desc', e.target.value.toUpperCase())"
        @blur="e => gb.updItem(item.id, 'desc', e.target.value.toUpperCase())"
      />
    </div>

    <!-- PURITY + GROSS -->
    <div class="m-ir">
      <div class="m-if">
        <label>Purity</label>
        <select :value="item.purity" @change="e => gb.updItem(item.id, 'purity', e.target.value)">
          <option value="" disabled>Select...</option>
          <option v-for="p in PURITY_LIST" :key="p" :value="p">{{ p }}</option>
        </select>
      </div>
      <div class="m-if">
        <label>Gross Wt (g)</label>
        <div class="m-gw-wrap">
          <input
            type="text"
            :value="gDisp"
            placeholder="0.000"
            style="text-align: right"
            @input="e => { gDisp = e.target.value; gCur = e.target.value; gDirty = true }"
            @blur="onGrossBlur"
            @keydown.enter="e => e.target.blur()"
          />
          <button v-if="hasDed" class="m-ded-btn on" @click="gb.clearDed(item.id)">✕ Ded</button>
          <button v-else class="m-ded-btn" @click="gb.dedModal.value = { ...item, idx: idx + 1 }">−</button>
        </div>
      </div>
    </div>

    <!-- NET + RATE -->
    <div class="m-ir">
      <div class="m-if">
        <label>Net Wt (g)</label>
        <div :class="['m-net-ro', hasDed ? 'ded' : '']">{{ fmtWtRaw(item.net) }}</div>
      </div>
      <div class="m-if">
        <label>Rate (RM/g)</label>
        <div class="m-rt-wrap">
          <div v-if="isLocked" class="m-rt-locked">{{ rDisp }}</div>
          <input v-else type="text" placeholder="0.00"
            :value="rDisp"
            style="text-align: right"
            @input="e => { rDisp = e.target.value; rCur = e.target.value; rDirty = true }"
            @blur="onRateBlur"
            @keydown.enter="e => e.target.blur()"
          />
          <!-- Lock button — only if dealer and lock available/assigned -->
          <button
            v-if="hasLock || isLocked"
            :class="['m-lk-btn', isLocked ? 'on' : '']"
            @click="toggleLockPop"
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <rect x="3" y="7" width="10" height="7" rx="1.5" :stroke="isLocked ? '#C9920A' : 'currentColor'" stroke-width="1.2"/>
              <path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2" :stroke="isLocked ? '#C9920A' : 'currentColor'" stroke-width="1.2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- AMOUNT + BAG -->
    <div class="m-amt-row">
      <div class="m-if" style="flex: 1; margin-bottom: 0">
        <label>Amount (RM)</label>
        <div v-if="isLocked" class="m-amt-locked">{{ aDisp }}</div>
        <input v-else class="m-amt-input" type="text" placeholder="0.00"
          :value="aDisp"
          @input="e => { aDisp = e.target.value; aCur = e.target.value; aDirty = true }"
          @blur="onAmountBlur"
          @keydown.enter="e => e.target.blur()"
        />
      </div>
      <!-- Bag button — hidden when Not In Hand -->
      <button
        v-if="gb.showBag.value"
        :class="['m-bg-btn', hasBagOverride ? 'set' : '']"
        @click="toggleBagPop"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M2.5 4.5h11l-1.5 8h-8l-1.5-8z" :stroke="hasBagOverride ? '#C9920A' : 'currentColor'" stroke-width="1.1" stroke-linejoin="round"/>
          <path d="M5.5 4.5V3.5a2.5 2.5 0 0 1 5 0v1" :stroke="hasBagOverride ? '#C9920A' : 'currentColor'" stroke-width="1.1" stroke-linecap="round"/>
        </svg>
      </button>
      <BagPopover
        v-if="gb.showBag.value && gb.bagPop.value?.itemId === item.id"
        :item="item"
        :pos="gb.bagPop.value.pos"
        @select="bag => { gb.updItem(item.id, 'bag', bag); gb.bagPop.value = null }"
      />
    </div>

    <!-- LOCK POPOVER -->
    <LockPopover
      v-if="gb.lockPop.value?.itemId === item.id"
      :item="item"
      :activeLocks="gb.locks.value"
      :pos="gb.lockPop.value.pos"
      :getLockRem="gb.getLockRem"
      @apply="gb.applyLock"
      @remove="gb.removeLock"
    />

    <!-- OVERAGE -->
    <div v-if="showOvg" style="margin-top: 8px; padding: 8px 10px; background: #FFFBEB; border-radius: var(--radius-sm); border: 1px solid var(--gold-border); font-size: 12px">
      <div style="color: #92600A; font-weight: 600; margin-bottom: 4px">⚠️ Exceeds {{ item.lockId }} by {{ ovgAmt.toFixed(3) }}g</div>
      <div style="display: flex; gap: 6px">
        <button class="overage-btn keep" style="flex: 1; text-align: center" @click="gb.keepRate(item.id)">✅ Keep rate</button>
        <button class="overage-btn split" style="flex: 1; text-align: center" @click="gb.splitExcess(item.id)">✂️ Split</button>
      </div>
    </div>

    <!-- NOTES (deduction + bag override) -->
    <div v-if="dedNote || hasBagOverride" class="m-inote">
      <span v-if="dedNote">↳ Deductions: {{ dedNote }}</span>
      <span v-if="hasBagOverride">↳ Bag: {{ item.bag }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, inject, nextTick, onMounted } from 'vue'
import { PURITY_LIST } from '../../../constants/index.js'
import { fmtRM, fmtWtRaw, fmtOnBlur, dedNoteText } from '../../../utils/formatters.js'
import LockPopover from '../shared/LockPopover.vue'
import BagPopover  from '../shared/BagPopover.vue'

const props = defineProps({
  item:       { type: Object,  required: true },
  idx:        { type: Number,  required: true },
  isLastAdded:{ type: Boolean, default: false }
})

const gb = inject('gb')
const descRef = ref(null)

// ── LOCAL DISPLAY STATE (same isDirty pattern as desktop ItemRow) ──
let gDisp = ref(props.item.gross > 0  ? fmtWtRaw(props.item.gross) : '')
let rDisp = ref(props.item.rate > 0   ? fmtRM(props.item.rate)     : '')
let aDisp = ref(props.item.amount > 0 ? fmtRM(props.item.amount)   : '')
let gCur = ref(gDisp.value)
let rCur = ref(rDisp.value)
let aCur = ref(aDisp.value)
let gDirty = ref(false)
let rDirty = ref(false)
let aDirty = ref(false)

watch(() => props.item.gross,  (v) => { if (!gDirty.value) { gDisp.value = v > 0 ? fmtWtRaw(v) : ''; gCur.value = gDisp.value } })
watch(() => props.item.rate,   (v) => { if (!rDirty.value) { rDisp.value = v > 0 ? fmtRM(v) : '';     rCur.value = rDisp.value } })
watch(() => props.item.amount, (v) => { if (!aDirty.value) { aDisp.value = v > 0 ? fmtRM(v) : '';     aCur.value = aDisp.value } })

onMounted(() => {
  if (props.isLastAdded && descRef.value) descRef.value.focus()
})

// ── COMPUTED ──
const hasDed        = computed(() => props.item.deds && props.item.deds.length > 0)
const isLocked      = computed(() => !!props.item.lockId)
const hasLock       = computed(() =>
  gb.custIsDealer.value &&
  gb.locks.value.some(l =>
    l.purity === props.item.purity &&
    ['Active', 'Expiring', 'Overdue'].includes(l.status)
  )
)
const dedNote       = computed(() => dedNoteText(props.item.deds))
const hasBagOverride = computed(() => props.item.bag && props.item.bag !== gb.defBag.value)
const showOvg = computed(() => {
  if (!isLocked.value || props.item.overageAck) return false
  const net = props.item.net || props.item.gross || 0
  if (!net) return false
  return (net - gb.getLockRem(props.item.lockId, props.item.id)) > 0.0005
})
const ovgAmt = computed(() => {
  if (!showOvg.value) return 0
  return (props.item.net || props.item.gross || 0) - gb.getLockRem(props.item.lockId, props.item.id)
})

// ── CALC ──
const commitCalc = (field, gv, rv, av) => {
  const g = field === 'gross'  ? gv : gCur.value
  const r = field === 'rate'   ? rv : rCur.value
  const a = field === 'amount' ? av : aCur.value
  gb.recalc(props.item.id, field, g.replace(/,/g,''), r.replace(/,/g,''), a.replace(/,/g,''))
}
const onGrossBlur  = (e) => { gDirty.value = false; const fmt = fmtOnBlur(e.target.value, true);  gDisp.value = fmt; gCur.value = fmt; commitCalc('gross',  fmt, rCur.value, aCur.value) }
const onRateBlur   = (e) => { rDirty.value = false; if (isLocked.value) return; const fmt = fmtOnBlur(e.target.value, false); rDisp.value = fmt; rCur.value = fmt; commitCalc('rate',   gCur.value, fmt, aCur.value) }
const onAmountBlur = (e) => { aDirty.value = false; if (isLocked.value) return; const fmt = fmtOnBlur(e.target.value, false); aDisp.value = fmt; aCur.value = fmt; commitCalc('amount', gCur.value, rCur.value, fmt) }

// ── POPOVER TOGGLES ──
const toggleLockPop = (e) => {
  if (!hasLock.value && !isLocked.value) return
  const rect = e.currentTarget.getBoundingClientRect()
  gb.lockPop.value = gb.lockPop.value?.itemId === props.item.id
    ? null : { itemId: props.item.id, pos: { top: rect.bottom + 6, left: Math.max(10, rect.right - 300) } }
}
const toggleBagPop = (e) => {
  const rect = e.currentTarget.getBoundingClientRect()
  gb.bagPop.value = gb.bagPop.value?.itemId === props.item.id
    ? null : { itemId: props.item.id, pos: { top: rect.bottom + 4, left: Math.max(10, rect.right - 220) } }
}
</script>
