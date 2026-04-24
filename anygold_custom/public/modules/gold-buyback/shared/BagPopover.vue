<template>
  <teleport to="body">
    <div class="bag-mini-dd" :style="{ top: pos.top + 'px', left: pos.left + 'px', display: 'block' }">
      <div class="bag-mini-hdr">Assign Bag for This Item</div>
      <div style="max-height: 114px; overflow-y: auto">
        <div
          v-for="o in opts" :key="o.label"
          :class="['bag-mini-opt', item.bag === o.val ? 'selected' : '']"
          @click="$emit('select', o.val)"
        >
          <span class="bag-dot"></span>{{ o.label }}
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { computed } from 'vue'
import { BAG_OPTIONS } from '../../../constants/index.js'

const props = defineProps({
  item: { type: Object, required: true },
  pos:  { type: Object, required: true }
})
defineEmits(['select'])

// First option is "Default" (null val), rest are the actual bags
const opts = computed(() => [
  { val: null, label: 'Default (WS-Main Bag)' },
  ...BAG_OPTIONS.slice(1).map(b => ({ val: b, label: b }))
])
</script>
