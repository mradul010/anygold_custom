<template>
  <teleport to="body">
    <div class="lock-popover" :style="{ top: pos.top + 'px', left: pos.left + 'px' }">
      <div class="lock-popover-hdr">Available Locks for {{ item.purity }}</div>
      <div v-if="!matching.length" style="padding: 14px; font-size: 12px; color: var(--text-muted)">
        No available locks for this purity.
      </div>
      <div v-else style="max-height: 216px; overflow-y: auto">
        <div v-for="lk in matching" :key="lk.id" class="lock-option">
          <div class="lock-option-info">
            <div class="lock-option-id">
              {{ lk.id }}
              <span v-if="lk.status === 'Active'"   class="lock-status active">🟢 Active</span>
              <span v-else-if="lk.status === 'Expiring'" class="lock-status expiring">🟡 Expiring</span>
              <span v-else class="lock-status overdue">🟠 Overdue</span>
            </div>
            <div class="lock-option-detail">RM {{ fmtRM(lk.rate) }}/g · {{ remWeight(lk.id) }}g remaining</div>
            <div class="lock-option-time">Locked {{ lk.time }}</div>
          </div>
          <button v-if="item.lockId === lk.id" class="lock-apply-btn remove" @click="$emit('remove', item.id)">Remove</button>
          <button v-else class="lock-apply-btn" @click="$emit('apply', item.id, lk)">Apply</button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { computed } from 'vue'
import { fmtRM } from '../../../utils/formatters.js'

const props = defineProps({
  item:        { type: Object,   required: true },
  activeLocks: { type: Array,    default: () => [] },
  pos:         { type: Object,   required: true },
  getLockRem:  { type: Function, required: true }
})
defineEmits(['apply', 'remove'])

const matching = computed(() =>
  props.activeLocks.filter(l =>
    l.purity === props.item.purity &&
    ['Active', 'Expiring', 'Overdue'].includes(l.status)
  )
)

const remWeight = (lockId) =>
  props.getLockRem(lockId, props.item.id).toFixed(3)
</script>
