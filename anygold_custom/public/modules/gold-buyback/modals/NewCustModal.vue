<!--
  NewCustModal — used by the MOBILE layout in GoldBuybackPage.vue.
  Desktop uses the modal built into CustomerSection.vue (teleported).
  Both share the same backend API: create_goldbuyback_customer.

  Emits:
    @close           — user cancelled or ESC
    @save(custObj)   — customer saved; custObj is the app-shape customer object
-->
<template>
  <teleport to="body">
    <div class="gb-modal-overlay" @mousedown.self="close">
      <div class="gb-modal-box" role="dialog" aria-modal="true" aria-labelledby="mob-new-cust-title">

        <!-- Header -->
        <div class="gb-modal-header">
          <h3 id="mob-new-cust-title">
            New Customer
            <span v-if="isMalaysian" class="nc-badge-malaysian">🇲🇾 Malaysian</span>
            <span v-else class="nc-badge-foreigner">🌍 Non-Malaysian</span>
          </h3>
          <button class="gb-modal-close" @click="close" aria-label="Close">×</button>
        </div>

        <!-- Body -->
        <div class="gb-modal-body">

          <div v-if="formErrors.length" class="nc-errors">
            <div v-for="e in formErrors" :key="e" class="nc-error">⚠ {{ e }}</div>
          </div>

          <!-- Customer Name -->
          <div class="nc-f">
            <label>Customer Name <span class="req">*</span></label>
            <input type="text" class="field-input" v-model="form.customer_name"
              placeholder="Full legal name" style="text-transform: uppercase" autocomplete="off" />
          </div>

          <!-- Nationality + Customer Type -->
          <div class="grid-2" style="gap: 12px">
            <div class="nc-f" style="margin-bottom: 0">
              <label>Nationality <span class="req">*</span></label>
              <select class="field-input" v-model="form.nationality" @change="onNationalityChange">
                <option value="Malaysian">Malaysian</option>
                <option value="Non-Malaysian / Foreigner">Non-Malaysian / Foreigner</option>
              </select>
            </div>
            <div class="nc-f" style="margin-bottom: 0">
              <label>Customer Type <span class="req">*</span></label>
              <select class="field-input" v-model="form.customer_type">
                <option>Individual</option>
                <option>Dealer</option>
                <option>Company</option>
              </select>
            </div>
          </div>

          <div class="nc-section-divider">Identity</div>

          <div v-if="isMalaysian" class="nc-f">
            <label>IC Number <span class="req">*</span></label>
            <input type="text" class="field-input"
              :value="fmtIC(form.ic_number)"
              @input="e => { form.ic_number = fmtIC(e.target.value) }"
              placeholder="e.g. 900101-14-1234" autocomplete="off" />
          </div>

          <template v-if="!isMalaysian">
            <div class="nc-f">
              <label>Passport / ID Number <span class="req">*</span></label>
              <input type="text" class="field-input" v-model="form.other_id_number"
                placeholder="Passport or ID number" autocomplete="off" />
            </div>
            <div class="nc-f">
              <label>Country / ID Type <span class="req">*</span></label>
              <input type="text" class="field-input" v-model="form.other_id_type"
                placeholder="e.g. Singapore, India" autocomplete="off" />
            </div>
          </template>

          <div class="nc-section-divider">Contact</div>

          <div class="nc-f">
            <label>Mobile Number <span class="req">*</span></label>
            <input type="tel" class="field-input" v-model="form.mobile_no"
              placeholder="e.g. 0123456789" autocomplete="off" />
          </div>

          <div class="nc-section-divider">Banking (Optional)</div>

          <div class="grid-2" style="gap: 12px">
            <div class="nc-f" style="margin-bottom: 0">
              <label>Bank Name</label>
              <input type="text" class="field-input" v-model="form.bank_name" placeholder="e.g. Maybank" />
            </div>
            <div class="nc-f" style="margin-bottom: 0">
              <label>Account Number</label>
              <input type="text" class="field-input" v-model="form.bank_account_number" placeholder="Optional" />
            </div>
          </div>

          <div class="nc-section-divider">{{ photoLabel }}</div>

          <div class="nc-f" style="margin-bottom: 0">
            <div :class="['nc-photo-upload', form.photo_url ? 'has-file' : '']" @click="triggerPhotoUpload">
              <div v-if="photoUploading" class="nc-uploading">Uploading…</div>
              <template v-else-if="form.photo_url">
                <div class="nc-photo-icon">✅</div>
                <div class="nc-photo-name">{{ form.photo_filename }}</div>
              </template>
              <template v-else>
                <div class="nc-photo-icon">📎</div>
                <div class="nc-photo-hint">Click to upload JPG or PNG</div>
              </template>
            </div>
            <input ref="photoInputRef" type="file" accept="image/jpeg,image/png,image/jpg"
              style="display: none" @change="onPhotoSelect" />
          </div>

        </div>

        <!-- Footer -->
        <div class="gb-modal-footer">
          <button class="btn btn-outline" @click="close" :disabled="saving">Cancel</button>
          <button class="btn btn-gold" @click="submit" :disabled="saving">
            {{ saving ? 'Saving…' : 'Save Customer' }}
          </button>
        </div>

      </div>
    </div>
  </teleport>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'

const emit = defineEmits(['close', 'save'])

// ── Form state ──
const saving         = ref(false)
const formErrors     = ref([])
const photoInputRef  = ref(null)
const photoUploading = ref(false)

const form = reactive({
  customer_name:       '',
  nationality:         'Malaysian',
  customer_type:       'Individual',
  mobile_no:           '',
  ic_number:           '',   // Malaysian IC — submitted as 'malaysian_id'
  other_id_type:       '',   // Non-Malaysian country/ID type — matches DB field 'other_id_type'
  other_id_number:     '',   // Non-Malaysian passport/ID — matches DB field 'other_id_number'
  bank_name:           '',
  bank_account_number: '',
  photo_url:           '',
  photo_filename:      '',
})

// ── Computed ──
const isMalaysian = computed(() => form.nationality === 'Malaysian')
const photoLabel  = computed(() => isMalaysian.value ? 'Customer IC Photo (Optional)' : 'Passport / ID Photo (Optional)')

// ── Nationality change ──
const onNationalityChange = () => {
  if (isMalaysian.value) { form.other_id_type = ''; form.other_id_number = '' }
  else                   { form.ic_number = '' }
}

// ── IC auto-format ──
const fmtIC = (raw) => {
  const d = (raw || '').replace(/\D/g, '').slice(0, 12)
  if (d.length <= 6) return d
  if (d.length <= 8) return d.slice(0, 6) + '-' + d.slice(6)
  return d.slice(0, 6) + '-' + d.slice(6, 8) + '-' + d.slice(8)
}

// ── Photo upload ──
const triggerPhotoUpload = () => photoInputRef.value?.click()

const onPhotoSelect = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  form.photo_filename  = file.name
  photoUploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', file, file.name)
    fd.append('is_private', '0')
    fd.append('folder', 'Home/Attachments')
    const res  = await fetch('/api/method/upload_file', {
      method: 'POST', body: fd,
      headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token },
    })
    const data = await res.json()
    form.photo_url = data.message?.file_url || ''
  } catch (err) {
    console.warn('Photo upload failed:', err)
  } finally {
    photoUploading.value = false
  }
}

// ── Validation ──
const validate = () => {
  const errs = []
  if (!form.customer_name.trim()) errs.push('Customer Name is required.')
  if (!form.nationality)          errs.push('Nationality is required.')
  if (!form.customer_type)        errs.push('Customer Type is required.')
  if (!form.mobile_no.trim())     errs.push('Mobile Number is required.')
  if (isMalaysian.value) {
    if (!form.ic_number.replace(/\D/g, ''))
      errs.push('IC Number is required for Malaysian customers.')
  } else {
    if (!form.other_id_number.trim()) errs.push('Passport / ID Number is required.')
    if (!form.other_id_type.trim())   errs.push('Country / ID Type is required.')
  }
  return errs
}

// ── Submit ──
const submit = async () => {
  const errs = validate()
  if (errs.length) { formErrors.value = errs; return }
  formErrors.value = []
  saving.value     = true

  try {
    const payload = {
      customer_name:       form.customer_name.trim().toUpperCase(),
      nationality:         form.nationality,
      customer_type:       form.customer_type,
      mobile_no:           form.mobile_no.trim(),
      bank_name:           form.bank_name.trim(),
      bank_account_number: form.bank_account_number.trim(),
      customer_photo:      form.photo_url,
    }
    if (isMalaysian.value) {
      payload.malaysian_id    = form.ic_number.trim()
      payload.other_id_type   = ''
      payload.other_id_number = ''
    } else {
      payload.malaysian_id    = ''
      payload.other_id_type   = form.other_id_type.trim()
      payload.other_id_number = form.other_id_number.trim()
    }

    const res  = await frappe.call({
      method: 'anygold_custom.api.GoldBuyBack.customer.create_goldbuyback_customer',
      args:   { data: JSON.stringify(payload) },
    })
    const data = res.message

    if (!data?.success) {
      formErrors.value = [data?.message || 'Failed to save customer.']
      return
    }

    if (data.duplicate) frappe.show_alert({ message: data.message, indicator: 'orange' }, 6)
    else                frappe.show_alert({ message: 'Customer saved successfully!', indicator: 'green' }, 4)

    const c = data.customer
    const custObj = {
      name:        c.customer_name       || '',
      customer_id: c.name,
      ic:          c.ic_number           || '',
      passport:    c.passport_number     || '',
      nationality: c.nationality         || 'Malaysian',
      country:     c.country             || '',
      type:        c.customer_group      || form.customer_type,
      mobile:      c.mobile_no           || form.mobile_no,
      bank:        c.bank_name           || '',
      acc:         c.bank_account_number || '',
      advance:     0,
      locks:       0,
    }
    emit('save', custObj)

  } catch (err) {
    formErrors.value = [err.message || 'An unexpected error occurred.']
  } finally {
    saving.value = false
  }
}

// ── Close ──
const close = () => { if (!saving.value) emit('close') }

// ESC to close
const onKey = (e) => { if (e.key === 'Escape') close() }
onMounted(()   => document.addEventListener('keydown', onKey))
onUnmounted(() => document.removeEventListener('keydown', onKey))
</script>
