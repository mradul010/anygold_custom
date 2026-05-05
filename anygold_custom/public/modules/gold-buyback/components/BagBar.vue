<!-- BagBar.vue -->
<template>
  <div>
    <!-- Item in Hand: show bag selector -->
    <div v-if="!gb.niH.value" class="bag-bar">
      <label>Bag Destination</label>
      <select class="field-input" style="max-width: 260px" v-model="gb.defBag.value">
        <option v-for="b in gb.bagOptions.value" :key="b">{{ b }}</option>
        <option>+ Create New Bag</option>
      </select>
    </div>
    <!-- Not In Hand: auto-assigns to WS-Not In Hand -->
    <div v-else class="bag-bar" style="background: var(--bg); opacity: 0.7">
      <label>Bag Destination</label>
      <span style="font-size: 13px; color: var(--text-muted); font-weight: 500">
        WS-Not In Hand (auto-assigned)
      </span>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue'

const gb = inject('gb')
</script>
