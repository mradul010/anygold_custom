<template>
  <teleport to="body">
    <div class="overlay">
      <div class="modal" style="width: 440px">
        <div class="modal-hdr">
          <h3>⚠️ Confirm Submission</h3>
          <button class="modal-x" @click="$emit('close')">✕</button>
        </div>
        <div class="modal-body">
          <div style="font-size: 13px; line-height: 1.7">
            <div style="margin-bottom: 10px">The following item lines have unresolved lock overages:</div>
            <div style="background: var(--bg); border-radius: var(--radius-sm); padding: 10px 12px; font-size: 12px; font-family: monospace; white-space: pre-line; color: var(--text-muted); margin-bottom: 10px">{{ lines }}</div>
            <div style="font-size: 12px; color: var(--text-muted)">The locked rate will apply to the full net weight including the overage. Proceed?</div>
          </div>
        </div>
        <div class="modal-ftr">
          <button class="btn btn-outline" @click="$emit('close')">Cancel</button>
          <button class="btn btn-gold" @click="$emit('confirm')">Proceed &amp; Save</button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
defineProps({ lines: { type: String, default: '' } })
defineEmits(['close', 'confirm'])
</script>
