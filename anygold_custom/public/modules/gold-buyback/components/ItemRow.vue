<template>
  <tr class="item-row">

    <!-- # -->
    <td style="width:30px; vertical-align:top; padding:5px 4px; text-align:center">
      <div style="display:flex; align-items:center; justify-content:center; min-height:30px">
        <span class="row-num">{{ idx + 1 }}</span>
      </div>
    </td>

    <!-- DESCRIPTION -->
    <td style="position:relative; vertical-align:top; padding:5px 4px">
      <div style="display:flex; align-items:center; min-height:30px">
        <DescCombobox
          style="flex:1; min-width:0"
          :value="item.desc"
          :autoFocus="isLastAdded"
          @change="v => gb.updItem(item.id, 'desc', v)"
        />
      </div>
    </td>

    <!-- PURITY -->
    <td style="width:90px; vertical-align:top; padding:5px 4px">
      <!-- control row -->
      <div style="display:flex; align-items:center; min-height:30px">
        <PurityCombobox
          style="flex:1; min-width:0"
          :value="item.purity"
          :purityList="purityList"
          @change="v => gb.updItem(item.id, 'purity', v)"
          @purity-created="gb.refreshPurityList && gb.refreshPurityList()"
        />
      </div>
      <!-- WG checkbox -->
      <div style="margin-top:3px">
        <label style="display:flex; align-items:center; gap:2px; font-size:10px; color:var(--text-muted); cursor:pointer; user-select:none; white-space:nowrap">
          <input
            type="checkbox"
            :checked="item.is_white_gold"
            @change="e => gb.updItem(item.id, 'is_white_gold', e.target.checked)"
            style="width:11px; height:11px; cursor:pointer; margin:0"
          />
          WG
        </label>
      </div>
    </td>

    <!-- GROSS WEIGHT -->
    <td style="width:130px; vertical-align:top; padding:5px 4px">
      <div style="display:flex; align-items:center; gap:4px; min-height:30px">
        <input
          type="text"
          class="tbl-input"
          style="flex:1; min-width:0"
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
    <td style="width:90px; vertical-align:top; padding:5px 4px 5px 8px">
      <div style="display:flex; align-items:center; min-height:30px">
        <span :class="['net-cell', hasDed ? 'deducted' : '']">{{ fmtWtRaw(item.net) }}</span>
      </div>
    </td>

    <!-- RATE -->
    <td style="width:110px; vertical-align:top; padding:5px 4px">
      <div style="display:flex; align-items:center; min-height:30px">
        <input
          type="text"
          :class="['tbl-input', isLocked ? 'locked' : '']"
          style="width:100%"
          placeholder="0.00"
          :value="rDisp"
          :readonly="isLocked"
          @input="e => { if (!isLocked) { rDisp = e.target.value; rCur = e.target.value; rDirty = true } }"
          @blur="onRateBlur"
          @keydown.enter="e => e.target.blur()"
        />
      </div>
    </td>

    <!-- LOCK ICON (dealer only) -->
    <td v-if="gb.custIsDealer.value" style="width:32px; vertical-align:top; padding:5px 2px">
      <div style="display:flex; align-items:center; justify-content:center; min-height:30px; position:relative">
        <button
          v-if="hasLock || isLocked"
          :class="['lock-icon-btn', isLocked ? 'assigned' : '']"
          style="margin:0"
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
    <td v-else style="width:32px; vertical-align:top; padding:5px 2px"></td>

    <!-- AMOUNT -->
    <td style="width:120px; vertical-align:top; padding:5px 8px 5px 4px">
      <div style="display:flex; align-items:center; min-height:30px">
        <input
          type="text"
          :class="['tbl-input', isLocked ? 'locked' : '']"
          style="width:100%"
          placeholder="0.00"
          :value="aDisp"
          :readonly="isLocked"
          @input="e => { if (!isLocked) { aDisp = e.target.value; aCur = e.target.value; aDirty = true } }"
          @blur="onAmountBlur"
          @keydown.enter="e => e.target.blur()"
        />
      </div>
    </td>

    <!-- BAG + REMOVE -->
    <td style="width:60px; vertical-align:top; padding:5px 4px">
      <div style="display:flex; align-items:center; justify-content:center; gap:4px; min-height:30px; position:relative">
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
  <tr v-if="gb.showBag.value && item.bag && item.bag !== gb.defBag.value" style="border-bottom:1px solid var(--border)">
    <td></td>
    <td colspan="7" style="padding:2px 4px 8px; font-size:11px; color:var(--text-muted)">
      ↳ Bag: {{ item.bag }}
    </td>
    <td></td>
  </tr>

  <!-- DEDUCTION SUB-ROW -->
  <tr v-if="dedNote" style="border-bottom:1px solid var(--border)">
    <td></td>
    <td colspan="7" style="padding:2px 4px 8px; font-size:11px; color:var(--text-muted)">
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
import { ref, computed, watch, inject } from 'vue'
import { fmtRM, fmtWtRaw, fmtOnBlur, dedNoteText } from '../../../utils/formatters.js'
import PurityCombobox from '../shared/PurityCombobox.vue'
import DescCombobox   from '../shared/DescCombobox.vue'
import LockPopover    from '../shared/LockPopover.vue'
import BagPopover     from '../shared/BagPopover.vue'

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
