<template>
  <div style="position: relative">
    <input
      ref="inputRef"
      type="text"
      class="tbl-input desc"
      style="text-transform: uppercase"
      placeholder="e.g. CINCIN, MIX GOLD..."
      :value="text"
      @input="onInput"
      @focus="onFocus"
      @blur="onBlur"
      @keydown="onKeydown"
    />
    <teleport to="body">
      <div
        v-if="open && filtered.length"
        class="combobox-dd"
        :style="ddStyle"
      >
        <div
          v-for="s in filtered"
          :key="s.name"
          class="combobox-opt"
          :class="{ active: s.item_name === text || s.name === text }"
          @mousedown.prevent="commit(s)"
          @mouseenter="e => e.currentTarget.style.background = 'var(--gold-light)'"
          @mouseleave="e => e.currentTarget.style.background = ''"
        >{{ s.item_name || s.name }}</div>
        <div
          v-if="text.trim() && !filtered.some(s => (s.item_name || s.name).toUpperCase() === text.toUpperCase())"
          class="combobox-add"
          @mousedown.prevent="commitCustom"
        >+ Add "{{ text.toUpperCase() }}" to List</div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
// import { DESC_SUGGESTIONS } from '../../../constants/index.js'

const props = defineProps({
  value:     { type: String, default: '' },
  autoFocus: { type: Boolean, default: false }
})
const emit = defineEmits(['change'])

const inputRef = ref(null)
const text = ref(props.value || '')
const open = ref(false)
const ddStyle = ref({})
const suggestions = ref([])

watch(() => props.value, (v) => { text.value = v || '' })

const filtered = computed(() => {
  const q = text.value.toUpperCase()
  return q ? suggestions.value.filter(s => s.item_name.toUpperCase().includes(q) || s.name.toUpperCase().includes(q)) : suggestions.value.slice(0, 20)
})

const fetchSuggestions = async () => {
  if (suggestions.value.length) return

  try {
    const res = await frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "Item",
        fields: ["name", "item_name"],
        order_by: "modified desc",
        limit_page_length: 5
      }
    })
    suggestions.value = res.message || []
  } catch (e) {
    suggestions.value = []
  }
}

const openDD = () => {
  if (inputRef.value) {
    const rect = inputRef.value.getBoundingClientRect()
    ddStyle.value = {
      position: 'fixed',
      top:   rect.bottom + 2 + 'px',
      left:  rect.left + 'px',
      width: rect.width + 'px',
      maxHeight: '160px',
      zIndex: 500
    }
  }
  open.value = true
}

const commit = (s) => {
  const val = (s.item_name || s.name).toUpperCase()
  text.value = val
  emit('change', val)
  open.value = false
}

const commitCustom = () => {
  if (text.value.trim()) commit(text.value)
}

const onInput = (e) => {
  text.value = e.target.value.toUpperCase()
  openDD()
}

const onFocus = (e) => {
  e.target.select()
  fetchSuggestions()
  openDD()
}

const onBlur = () => {
  setTimeout(() => { open.value = false }, 150)
  emit('change', text.value)
}

const onKeydown = (e) => {
  if (e.key === 'Enter' || e.key === 'Tab') {
    if (open.value && filtered.value.length > 0) {
      e.preventDefault()
      commit(filtered.value[0])
    } else {
      emit('change', text.value)
      open.value = false
      if (e.key === 'Enter') e.target.blur()
    }
  }
  if (e.key === 'Escape') { open.value = false; e.target.blur() }
}

// Auto-focus on mount if requested (new item added)
if (props.autoFocus) {
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.focus()
      inputRef.value.select()
      fetchSuggestions()
      openDD()
    }
  })
}
</script>
