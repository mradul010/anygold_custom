<template>
  <teleport to="body">
    <div class="gb-overlay">
      <div class="gb-modal" style="width: 400px">
        <div class="modal-hdr">
          <h3>Deductions — Item {{ item.idx }}</h3>
          <button class="modal-x" @click="$emit('close')">✕</button>
        </div>
        <div class="modal-body">
          <div class="gross-display">
            <span class="lbl">Gross Weight</span>
            <span class="val">{{ fmtWt(gross) }}</span>
          </div>
          <div v-for="(row, i) in rows" :key="i" class="ded-row">
            <select :value="row.type" @change="e => upd(i, 'type', e.target.value)">
              <option>Stones</option>
              <option>Enamel</option>
              <option>Spring/Clasp</option>
              <option>Others</option>
            </select>
            <input v-if="row.type === 'Others'" type="text"
              placeholder="Describe..." :value="row.desc || ''"
              @input="e => upd(i, 'desc', e.target.value)" />
            <input type="text" placeholder="0.000"
              :value="row.w || ''"
              @input="e => upd(i, 'w', e.target.value.replace(/[^0-9.]/g, ''))"
              @blur="e => { const v = parseFloat(e.target.value); upd(i, 'w', isNaN(v) ? '' : v.toFixed(3)) }"
              @keydown.enter="e => e.target.blur()"
              style="text-align: right"
            />
            <button class="del-btn" @click="del(i)">✕</button>
          </div>
          <button @click="add" style="background: none; border: none; cursor: pointer; color: var(--blue); font-size: 12px; font-weight: 500; padding: 6px 0; display: flex; align-items: center; gap: 4px">
            + Add Deduction
          </button>
          <div class="ded-sum">
            <div class="ded-sum-row"><span class="lbl">Total Deduction</span><span class="val">{{ fmtWt(tot) }}</span></div>
            <div class="ded-sum-row net"><span class="lbl">Net Weight</span><span class="val">{{ fmtWt(net) }}</span></div>
          </div>
        </div>
        <div class="modal-ftr">
          <button class="btn btn-outline" @click="$emit('close')">Cancel</button>
          <button class="btn btn-gold" @click="apply">Apply</button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { fmtWt } from '../../../utils/formatters.js'

const props = defineProps({ item: { type: Object, required: true } })
const emit  = defineEmits(['close', 'apply'])

const rows = ref(
  props.item.deds && props.item.deds.length
    ? props.item.deds.map(d => ({ ...d }))
    : [{ type: 'Stones', w: '', desc: '' }]
)

const gross = computed(() => parseFloat(props.item.gross) || 0)
const tot   = computed(() => rows.value.reduce((s, r) => s + (parseFloat(r.w) || 0), 0))
const net   = computed(() => Math.max(0, gross.value - tot.value))

const add = () => rows.value.push({ type: 'Stones', w: '', desc: '' })
const del = (i) => rows.value.splice(i, 1)
const upd = (i, f, v) => { rows.value[i] = { ...rows.value[i], [f]: v } }
const apply = () => emit('apply', rows.value)

// ESC to close
const onKey = (e) => { if (e.key === 'Escape') emit('close') }
onMounted(() => document.addEventListener('keydown', onKey))
onUnmounted(() => document.removeEventListener('keydown', onKey))
</script>
