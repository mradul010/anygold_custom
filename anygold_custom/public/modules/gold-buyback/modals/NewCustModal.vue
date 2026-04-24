<template>
  <teleport to="body">
    <div class="gb-overlay">
      <div class="gb-modal" style="width: 420px; max-height: 90vh; display: flex; flex-direction: column">
        <div class="gb-modal-hdr">
          <h3>New Customer</h3>
          <button class="gb-modal-x" @click="$emit('close')">✕</button>
        </div>
        <div class="gb-modal-body" style="overflow-y: auto; flex: 1">
          <div class="nc-f">
            <label>Customer Name <span class="req">*</span></label>
            <input type="text" placeholder="FULL NAME AS PER IC / PASSPORT"
              :value="d.name" @input="e => f('name', e.target.value.toUpperCase())"
              @keydown.enter="e => e.target.blur()" />
          </div>
          <div class="nc-f">
            <label>Nationality <span class="req">*</span></label>
            <select :value="d.nat" @change="e => { f('nat', e.target.value); f('ic', '') }">
              <option>Malaysian</option>
              <option>Non-Malaysian</option>
            </select>
          </div>
          <div v-if="!isMY" class="nc-f">
            <label>Country / Nationality <span class="req">*</span></label>
            <input type="text" placeholder="e.g. Indonesian, Bangladeshi..."
              :value="d.natText" @input="e => f('natText', e.target.value)"
              @keydown.enter="e => e.target.blur()" />
          </div>
          <div class="nc-f">
            <label>{{ isMY ? 'IC Number' : 'Passport No.' }} <span class="req">*</span></label>
            <input type="text"
              :placeholder="isMY ? 'e.g. 900101-14-5678' : 'e.g. A12345678'"
              :value="d.ic"
              :maxlength="isMY ? 14 : 30"
              @input="e => f('ic', isMY ? fmtIC(e.target.value) : e.target.value)"
              @keydown.enter="e => e.target.blur()" />
            <div v-if="isMY && d.ic.replace(/\D/g,'').length > 0 && d.ic.replace(/\D/g,'').length < 12"
              style="font-size: 11px; color: var(--text-subtle); margin-top: 3px">
              {{ d.ic.replace(/\D/g,'').length }}/12 digits
            </div>
          </div>
          <div class="nc-f">
            <label>Customer Type <span class="req">*</span></label>
            <select :value="d.type" @change="e => f('type', e.target.value)">
              <option>Individual</option>
              <option>Dealer</option>
              <option>Pawn Shop</option>
              <option>Company</option>
            </select>
          </div>
          <div class="nc-f">
            <label>Mobile Number <span class="req">*</span></label>
            <input type="text" placeholder="012-345 6789"
              :value="d.mobile"
              @input="e => f('mobile', fmtMobileStr(e.target.value.replace(/\D/g,'')))"
              @keydown.enter="e => e.target.blur()" />
          </div>
          <div class="nc-f">
            <label>Bank Name</label>
            <input type="text" placeholder="e.g. Maybank"
              :value="d.bank" @input="e => f('bank', e.target.value)"
              @keydown.enter="e => e.target.blur()" />
          </div>
          <div class="nc-f">
            <label>Bank Account Number</label>
            <input type="text" :value="d.acc"
              @input="e => f('acc', e.target.value)"
              @keydown.enter="e => e.target.blur()" />
          </div>
          <div class="nc-f">
            <label>{{ isMY ? 'Customer IC Photo' : 'Passport Photo' }}</label>
            <div class="upload-box" @click="triggerUpload">
              <div style="font-size: 24px; margin-bottom: 6px">📷</div>
              <div style="font-size: 12px; color: var(--text-muted)">
                Click to upload photo<br/><span style="font-size: 11px">JPG, PNG accepted</span>
              </div>
              <input ref="fileInput" type="file" accept="image/*" style="display: none"
                @change="e => photo = e.target.files[0]?.name || ''" />
            </div>
            <div v-if="photo" class="upload-preview">✓ {{ photo }}</div>
          </div>
        </div>
        <div class="gb-modal-ftr">
          <button class="btn btn-outline" @click="$emit('close')">Cancel</button>
          <button class="btn btn-primary" @click="save" :disabled="!d.name || !d.ic">Save Customer</button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { fmtMobileStr } from '../../../utils/formatters.js'

const emit = defineEmits(['close', 'save'])

const d = ref({ name: '', nat: 'Malaysian', natText: '', ic: '', type: 'Individual', mobile: '', bank: '', acc: '' })
const photo    = ref('')
const fileInput = ref(null)

const isMY = computed(() => d.value.nat === 'Malaysian')

const f = (k, v) => { d.value = { ...d.value, [k]: v } }

const fmtIC = (raw) => {
  const digits = raw.replace(/\D/g, '').slice(0, 12)
  if (digits.length <= 6) return digits
  if (digits.length <= 8) return digits.slice(0, 6) + '-' + digits.slice(6)
  return digits.slice(0, 6) + '-' + digits.slice(6, 8) + '-' + digits.slice(8)
}

const triggerUpload = () => fileInput.value?.click()

const save = () => {
  if (!d.value.name || !d.value.ic) return
  emit('save', d.value)
  emit('close')
}

// ESC to close
const onKey = (e) => { if (e.key === 'Escape') emit('close') }
onMounted(() => document.addEventListener('keydown', onKey))
onUnmounted(() => document.removeEventListener('keydown', onKey))
</script>
