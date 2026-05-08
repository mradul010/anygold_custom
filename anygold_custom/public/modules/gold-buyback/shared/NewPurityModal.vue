<template>
  <teleport to="body">
    <div class="npm-overlay" @mousedown.self="$emit('close')">
      <div class="npm-box">
        <div class="npm-header">
          <span>New Purity</span>
          <button class="npm-close" @click="$emit('close')">✕</button>
        </div>

        <div class="npm-body">
          <div class="npm-field">
            <label>Purity Code <span class="req">*</span></label>
            <input
              ref="codeRef"
              type="text"
              class="npm-input"
              placeholder="e.g. 892"
              v-model="code"
              @input="code = code.replace(/[^A-Za-z0-9]/g, '').toUpperCase()"
              maxlength="10"
            />
            <p v-if="dupMsg" class="npm-dup">{{ dupMsg }}</p>
          </div>

          <div class="npm-field">
            <label>XAU Coefficient <span class="npm-hint">(optional)</span></label>
            <input
              type="number"
              class="npm-input"
              placeholder="e.g. 0.892"
              v-model="xau"
              step="0.001"
              min="0"
              max="1"
            />
          </div>

          <div class="npm-field">
            <label>Description <span class="npm-hint">(optional)</span></label>
            <input
              type="text"
              class="npm-input"
              :placeholder="`e.g. Purity ${code || '892'}`"
              v-model="desc"
            />
          </div>

          <div v-if="preview.length" class="npm-preview">
            <span class="npm-preview-label">Items to create:</span>
            <span v-for="ic in preview" :key="ic" class="npm-item-badge">{{ ic }}</span>
          </div>

          <p v-if="errMsg" class="npm-err">{{ errMsg }}</p>
        </div>

        <div class="npm-footer">
          <button class="npm-btn cancel" @click="$emit('close')">Cancel</button>
          <button class="npm-btn create" :disabled="!code || saving" @click="submit">
            {{ saving ? 'Creating…' : 'Create Purity' }}
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'

const emit = defineEmits(['close', 'created'])

const code   = ref('')
const xau    = ref('')
const desc   = ref('')
const saving = ref(false)
const errMsg = ref('')
const dupMsg = ref('')
const codeRef = ref(null)

onMounted(() => nextTick(() => codeRef.value?.focus()))

const preview = computed(() => {
  if (!code.value) return []
  return [`WS-${code.value}-N`, `WS-${code.value}-WG`, `WS-${code.value}-EBTS`]
})

const submit = async () => {
  errMsg.value = ''
  dupMsg.value = ''
  if (!code.value.trim()) return

  saving.value = true
  try {
    const res = await frappe.call({
      method: 'anygold_custom.api.GoldBuyBack.items.create_purity_with_items',
      args: {
        purity_code:     code.value.trim(),
        description:     desc.value.trim(),
        xau_coefficient: parseFloat(xau.value) || 0,
      },
    })
    const data = res.message
    if (data.duplicate) {
      dupMsg.value = `"${data.purity_code}" already exists in Purity Master.`
      return
    }
    emit('created', {
      purity_code:     data.purity_code,
      xau_coefficient: parseFloat(xau.value) || 0,
    })
  } catch (e) {
    errMsg.value = e?.message || 'Failed to create purity.'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.npm-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1100;
}
.npm-box {
  background: var(--card-bg, #fff);
  border-radius: 10px;
  width: 360px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.22);
  display: flex; flex-direction: column;
  overflow: hidden;
}
.npm-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px 12px;
  border-bottom: 1px solid var(--border-color);
  font-weight: 700; font-size: 14px;
  background: var(--subtle-fg, #f9f5ee);
}
.npm-close {
  background: none; border: none; font-size: 14px;
  cursor: pointer; color: var(--text-muted); padding: 2px 6px;
}
.npm-close:hover { color: var(--text-color); }

.npm-body { padding: 18px; display: flex; flex-direction: column; gap: 14px; }

.npm-field { display: flex; flex-direction: column; gap: 4px; }
.npm-field label { font-size: 12px; font-weight: 600; color: var(--text-muted); }
.npm-hint { font-weight: 400; color: var(--text-subtle); }
.req { color: var(--red, #e74c3c); }
.npm-input {
  padding: 7px 10px; border: 1px solid var(--border-color);
  border-radius: 6px; font-size: 13px;
  background: var(--card-bg); color: var(--text-color);
  outline: none;
}
.npm-input:focus { border-color: var(--primary-color, #d4a843); }

.npm-preview {
  display: flex; flex-wrap: wrap; align-items: center; gap: 6px;
  padding: 8px 10px; background: var(--subtle-fg, #f9f5ee);
  border-radius: 6px; font-size: 12px;
}
.npm-preview-label { color: var(--text-muted); font-weight: 600; margin-right: 2px; }
.npm-item-badge {
  background: #e8f4ea; color: #2a6e35;
  border-radius: 4px; padding: 2px 7px; font-family: monospace; font-size: 11px;
}

.npm-dup { font-size: 11px; color: var(--orange, #e67e22); margin: 0; }
.npm-err { font-size: 11px; color: var(--red, #e74c3c); margin: 0; }

.npm-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 12px 18px;
  border-top: 1px solid var(--border-color);
  background: var(--subtle-fg, #f9f5ee);
}
.npm-btn {
  padding: 7px 18px; border-radius: 6px; font-size: 13px;
  font-weight: 600; cursor: pointer; border: none;
}
.npm-btn.cancel {
  background: var(--card-bg); border: 1px solid var(--border-color);
  color: var(--text-muted);
}
.npm-btn.cancel:hover { background: var(--fg-hover-color); }
.npm-btn.create {
  background: #c59a2f; color: #fff;
}
.npm-btn.create:hover:not(:disabled) { background: #b8891f; }
.npm-btn.create:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
