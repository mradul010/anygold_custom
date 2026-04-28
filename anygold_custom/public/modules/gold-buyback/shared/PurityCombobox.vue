<template>
  <div style="position: relative">
    <div style="position: relative; display: flex; align-items: center">
      <input
        ref="inputRef"
        type="text"
        class="tbl-input"
        style="padding-right: 22px"
        placeholder="e.g. 916"
        :value="text"
        @input="onInput"
        @focus="onFocus"
        @blur="onBlur"
        @keydown="onKeydown"
      />
      <span style="position: absolute; right: 7px; font-size: 9px; color: var(--text-subtle); pointer-events: none">▼</span>
    </div>
    <teleport to="body">
      <div
        v-if="open && filtered.length"
        class="combobox-dd"
        :style="ddStyle"
      >
        <div
          v-for="p in filtered"
          :key="p"
          class="combobox-opt"
          :class="{ active: p === text }"
          @mousedown.prevent="commit(p)"
        >{{ p }}</div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { PURITY_LIST } from '../../../constants/index.js'

const props = defineProps({ value: { type: String, default: '' } })
const emit  = defineEmits(['change'])

const inputRef = ref(null)
const text = ref(props.value || '')
const open = ref(false)
const ddStyle = ref({})

watch(() => props.value, (v) => { text.value = v || '' })

const filtered = computed(() => {
  if (!text.value) return PURITY_LIST
  return PURITY_LIST.filter(p => p.startsWith(text.value))
})

const openDD = () => {
  if (inputRef.value) {
    const rect = inputRef.value.getBoundingClientRect()
    ddStyle.value = {
      position: 'fixed',
      top:   rect.bottom + 2 + 'px',
      left:  rect.left + 'px',
      width: rect.width + 'px',
      maxHeight: '140px',
      zIndex: 500
    }
  }
  open.value = true
}

const commit = (v) => {
  text.value = v
  emit('change', v)
  open.value = false
}

const onInput = (e) => {
  text.value = e.target.value.replace(/[^0-9]/g, '')
  openDD()
}
const onFocus = (e) => { e.target.select(); openDD() }
const onBlur  = () => {
  setTimeout(() => { open.value = false }, 150)
  const match = PURITY_LIST.find(p => p === text.value)
  emit('change', match || text.value)
}
const onKeydown = (e) => {
  if ((e.key === 'Enter' || e.key === 'Tab') && open.value && filtered.value.length) {
    e.preventDefault(); commit(filtered.value[0])
  }
  if (e.key === 'Escape') { open.value = false; e.target.blur() }
}
</script>
