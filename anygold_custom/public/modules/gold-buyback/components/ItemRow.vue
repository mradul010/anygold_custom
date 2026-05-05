<template>
  <tr class="item-row">
    <!-- # -->
    <td class="row-num" style="width: 32px; text-align: center">{{ idx + 1 }}</td>

    <!-- DESCRIPTION — fixed dropdown, no free text -->
    <td style="position: relative; padding: 5px 4px">
      <div style="position: relative">
        <select
          ref="descRef"
          class="tbl-input desc"
          style="text-transform: uppercase; width: 100%; appearance: none; padding-right: 20px; cursor: pointer"
          :value="item.desc"
          @change="e => gb.updItem(item.id, 'desc', e.target.value)"
        >
          <option value="">— Select —</option>
          <option v-for="d in DESC_OPTIONS" :key="d" :value="d">{{ d }}</option>
        </select>
        <span style="position: absolute; right: 7px; top: 50%; transform: translateY(-50%); font-size: 9px; color: var(--text-subtle); pointer-events: none">▼</span>
      </div>
    </td>

    <!-- PURITY + item_code badge -->
    <td style="width: 80px; padding: 5px 4px">
      <PurityCombobox
        :value="item.purity"
        :purityList="purityList"
        @change="v => gb.updItem(item.id, 'purity', v)"
      />
      <!-- Item code badge — small indicator below purity -->
      <div
        v-if="item.item_code"
        style="font-size: 9px; color: var(--text-subtle); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 76px"
        :title="item.item_code"
      >{{ item.item_code }}</div>
    </td>

    <!-- GROSS WEIGHT -->
    <td style="width: 120px; padding: 5px 4px">
      <div style="display: flex; gap: 4px; align-items: center">
        <input
          type="text"
          class="tbl-input"
          placeholder="0.000"
          :value="gDisp"
          @input="e => { gDisp = e.target.value; gCur = e.target.value; gDirty = true }"
          @blur="onGrossBlur"
          @keydown.enter="e => e.target.blur()"
        />
        <button
          v-if="hasDed"
          class="deduct-btn on"
          @click="gb.clearDed(item.id)"
        >✕ Ded</button>
        <button
          v-else
          class="deduct-btn"
          @click="gb.dedModal.value = { ...item, idx: idx + 1 }"
        >−</button>
      </div>
    </td>

    <!-- NET WEIGHT -->
    <td style="width: 100px; padding-left: 8px">
      <span :class="['net-cell', hasDed ? 'deducted' : '']">{{ fmtWtRaw(item.net) }}</span>
    </td>

    <!-- RATE -->
    <td style="width: 110px; padding: 5px 4px; text-align: right">
      <input
        type="text"
        :class="['tbl-input', isLocked ? 'locked' : '']"
        style="width: 100%"
        placeholder="0.00"
        :value="rDisp"
        :readonly="isLocked"
        @input="e => { if (!isLocked) { rDisp = e.target.value; rCur = e.target.value; rDirty = true } }"
        @blur="onRateBlur"
        @keydown.enter="e => e.target.blur()"
      />
    </td>

    <!-- LOCK ICON (dealer only) -->
    <td v-if="gb.custIsDealer.value" style="width: 28px; text-align: center; vertical-align: middle; padding: 0 2px">
      <div style="position: relative">
        <button
          v-if="hasLock || isLocked"
          :class="['lock-icon-btn', isLocked ? 'assigned' : '']"
          style="margin: 0"
          @click="toggleLockPop"
        >🔒</button>
        <LockPopover
          v-if="gb.lockPop.value?.itemId === item.id"
          :item="item"
          :activeLocks="gb.locks.value"
          :pos="gb.lockPop.value.pos"
          :getLockRem="gb.getLockRem"
          @apply="gb.applyLock"
          @remove="gb.removeLock"
        />
      </div>
    </td>
    <td v-else style="width: 28px"></td>

    <!-- AMOUNT -->
    <td style="width: 130px; padding: 5px 4px; text-align: right; padding-right: 8px">
      <input
        type="text"
        :class="['tbl-input', isLocked ? 'locked' : '']"
        style="width: 100%"
        placeholder="0.00"
        :value="aDisp"
        :readonly="isLocked"
        @input="e => { if (!isLocked) { aDisp = e.target.value; aCur = e.target.value; aDirty = true } }"
        @blur="onAmountBlur"
        @keydown.enter="e => e.target.blur()"
      />
    </td>

    <!-- BAG + REMOVE -->
    <td style="text-align: center; white-space: nowrap; width: 56px">
      <div style="display: flex; align-items: center; justify-content: center; gap: 4px; position: relative">
        <button
          v-if="gb.showBag.value"
          :class="['bag-row-btn', item.bag ? 'set' : '']"
          @click="toggleBagPop"
        >🛍️</button>
        <BagPopover
          v-if="gb.showBag.value && gb.bagPop.value?.itemId === item.id"
          :item="item"
          :pos="gb.bagPop.value.pos"
          @select="onBagSelect"
        />
        <button class="rm-btn" @click="gb.removeItem(item.id)">✕</button>
      </div>
    </td>
  </tr>

  <!-- BAG OVERRIDE SUB-ROW -->
  <tr v-if="gb.showBag.value && item.bag && item.bag !== gb.defBag.value" style="border-bottom: 1px solid var(--border)">
    <td></td>
    <td colspan="7" style="padding: 2px 4px 8px; font-size: 11px; color: var(--text-muted)">
      ↳ Bag: {{ item.bag }}
    </td>
    <td></td>
  </tr>

  <!-- DEDUCTION SUB-ROW -->
  <tr v-if="dedNote" style="border-bottom: 1px solid var(--border)">
    <td></td>
    <td colspan="7" style="padding: 2px 4px 8px; font-size: 11px; color: var(--text-muted)">
      ↳ Deductions: {{ dedNote }}
    </td>
    <td></td>
  </tr>

  <!-- OVERAGE ROW -->
  <tr v-if="showOvg" class="overage-row">
    <td colspan="9">
      <div class="overage-inner">
        <span class="overage-msg">⚠️ Exceeds {{ item.lockId }} balance by {{ ovgAmt.toFixed(3) }}g</span>
        <button class="overage-btn keep" @click="gb.keepRate(item.id)">✅ Keep locked rate</button>
        <button class="overage-btn split" @click="gb.splitExcess(item.id)">✂️ Split excess to new line</button>
      </div>
    </td>
  </tr>
</template>

<script setup>
import { ref, computed, watch, inject, nextTick } from 'vue'
import { fmtRM, fmtWtRaw, fmtOnBlur, dedNoteText } from '../../../utils/formatters.js'
import { DESC_SUGGESTIONS } from '../../../constants/index.js'
import PurityCombobox from '../shared/PurityCombobox.vue'
import LockPopover    from '../shared/LockPopover.vue'
import BagPopover     from '../shared/BagPopover.vue'

const DESC_OPTIONS = DESC_SUGGESTIONS

const props = defineProps({
  item:        { type: Object,  required: true },
  idx:         { type: Number,  required: true },
  isLastAdded: { type: Boolean, default: false }
})

const gb = inject('gb')

// Purity list for PurityCombobox — driven by Purity Master fetch in composable.
// Falls back to the constant list if the fetch hasn't completed yet.
const purityList = computed(() =>
  gb.purityOptions.value.length
    ? gb.purityOptions.value.map(p => p.purity_code)
    : []
)

// ── LOCAL DISPLAY STATE ──
// Separate local state so the user can type freely without state updates
// resetting the cursor or value mid-edit.
const descRef = ref(null)
let gDisp = ref(props.item.gross  > 0 ? fmtWtRaw(props.item.gross)  : '')
let rDisp = ref(props.item.rate   > 0 ? fmtRM(props.item.rate)      : '')
let aDisp = ref(props.item.amount > 0 ? fmtRM(props.item.amount)    : '')

let gCur = ref(gDisp.value)
let rCur = ref(rDisp.value)
let aCur = ref(aDisp.value)

let gDirty = ref(false)
let rDirty = ref(false)
let aDirty = ref(false)

// Sync display when item state changes externally (lock, deduction apply, split, etc.)
watch(() => props.item.gross,  (v) => { if (!gDirty.value) { gDisp.value = v > 0 ? fmtWtRaw(v) : ''; gCur.value = gDisp.value } })
watch(() => props.item.rate,   (v) => { if (!rDirty.value) { rDisp.value = v > 0 ? fmtRM(v)     : ''; rCur.value = rDisp.value } })
watch(() => props.item.amount, (v) => { if (!aDirty.value) { aDisp.value = v > 0 ? fmtRM(v)     : ''; aCur.value = aDisp.value } })

// Auto-focus description select on new row
if (props.isLastAdded) {
  nextTick(() => { if (descRef.value) descRef.value.focus() })
}

// ── COMPUTED ──
const hasDed   = computed(() => props.item.deds && props.item.deds.length > 0)
const isLocked = computed(() => !!props.item.lockId)
const hasLock  = computed(() =>
  gb.custIsDealer.value &&
  gb.locks.value.filter(l =>
    l.purity === props.item.purity &&
    ['Active', 'Expiring', 'Overdue'].includes(l.status)
  ).length > 0
)
const dedNote = computed(() => dedNoteText(props.item.deds))
const showOvg = computed(() => {
  if (!isLocked.value || props.item.overageAck) return false
  const net = props.item.net || props.item.gross || 0
  if (!net) return false
  return (net - gb.getLockRem(props.item.lockId, props.item.id)) > 0.0005
})
const ovgAmt = computed(() => {
  if (!showOvg.value) return 0
  const net = props.item.net || props.item.gross || 0
  return net - gb.getLockRem(props.item.lockId, props.item.id)
})

// ── CALC COMMIT ──
const commitCalc = (field, gv, rv, av) => {
  const g = field === 'gross'  ? gv : gCur.value
  const r = field === 'rate'   ? rv : rCur.value
  const a = field === 'amount' ? av : aCur.value
  gb.recalc(
    props.item.id, field,
    g.replace(/,/g, ''),
    r.replace(/,/g, ''),
    a.replace(/,/g, '')
  )
}

const onGrossBlur = (e) => {
  gDirty.value = false
  const fmt = fmtOnBlur(e.target.value, true)
  gDisp.value = fmt; gCur.value = fmt
  commitCalc('gross', fmt, rCur.value, aCur.value)
}
const onRateBlur = (e) => {
  rDirty.value = false
  if (isLocked.value) return
  const fmt = fmtOnBlur(e.target.value, false)
  rDisp.value = fmt; rCur.value = fmt
  commitCalc('rate', gCur.value, fmt, aCur.value)
}
const onAmountBlur = (e) => {
  aDirty.value = false
  if (isLocked.value) return
  const fmt = fmtOnBlur(e.target.value, false)
  aDisp.value = fmt; aCur.value = fmt
  commitCalc('amount', gCur.value, rCur.value, fmt)
}

// ── BAG SELECTION ──
// bag and warehouse are the same value — the Warehouse document name.
// Passing null clears the per-item override; submit.py will use the document default.
const onBagSelect = (warehouseName) => {
  gb.pickBagForItem(props.item.id, warehouseName, warehouseName)
  gb.bagPop.value = null
}

// ── POPOVER TOGGLES ──
const toggleLockPop = (e) => {
  if (!hasLock.value && !isLocked.value) return
  const rect = e.currentTarget.getBoundingClientRect()
  gb.lockPop.value = gb.lockPop.value?.itemId === props.item.id
    ? null
    : { itemId: props.item.id, pos: { top: rect.bottom + 6, left: Math.max(10, rect.right - 300) } }
}
const toggleBagPop = (e) => {
  const rect = e.currentTarget.getBoundingClientRect()
  gb.bagPop.value = gb.bagPop.value?.itemId === props.item.id
    ? null
    : { itemId: props.item.id, pos: { top: rect.bottom + 4, left: Math.max(10, rect.right - 220) } }
}
</script>
