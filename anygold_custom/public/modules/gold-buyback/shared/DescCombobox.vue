<template>
  <div style="position: relative">
    <div style="position: relative; display: flex; align-items: center">
      <input
        ref="inputRef"
        type="text"
        class="tbl-input desc"
        style="text-transform: uppercase; padding-right: 22px; width: 100%"
        placeholder="— Select or type —"
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
          v-for="s in filtered"
          :key="s"
          class="combobox-opt"
          :class="{ active: s === text.toUpperCase() }"
          @mousedown.prevent="commit(s)"
        >{{ s }}</div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { DESC_SUGGESTIONS } from '../../../constants/index.js'

const props = defineProps({
  value:     { type: String, default: '' },
  autoFocus: { type: Boolean, default: false }
})
const emit = defineEmits(['change'])

const inputRef = ref(null)
const text     = ref(props.value || '')
const open     = ref(false)
const ddStyle  = ref({})

watch(() => props.value, (v) => { text.value = v || '' })

const filtered = computed(() => {
  const q = text.value.toUpperCase().trim()
  if (!q) return DESC_SUGGESTIONS
  return DESC_SUGGESTIONS.filter(s => s.includes(q))
})

const openDD = () => {
  if (inputRef.value) {
    const rect = inputRef.value.getBoundingClientRect()
    ddStyle.value = {
      position:  'fixed',
      top:       rect.bottom + 2 + 'px',
      left:      rect.left + 'px',
      width:     Math.max(rect.width, 160) + 'px',
      maxHeight: '180px',
      zIndex:    500,
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
  text.value = e.target.value.toUpperCase()
  e.target.value = text.value
  openDD()
}

const onFocus = (e) => {
  e.target.select()
  openDD()
}

const onBlur = () => {
  setTimeout(() => { open.value = false }, 150)
  emit('change', text.value)
}

const onKeydown = (e) => {
  if ((e.key === 'Enter' || e.key === 'Tab') && open.value && filtered.value.length) {
    e.preventDefault()
    commit(filtered.value[0])
  } else if (e.key === 'Enter') {
    emit('change', text.value)
    open.value = false
    e.target.blur()
  }
  if (e.key === 'Escape') { open.value = false; e.target.blur() }
}

if (props.autoFocus) {
  nextTick(() => {
    if (inputRef.value) { inputRef.value.focus(); inputRef.value.select() }
  })
}
</script>
