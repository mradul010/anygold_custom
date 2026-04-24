<!-- BagBar.vue -->
<template>
  <div>
    <!-- Item in Hand: show bag selector -->
    <div v-if="!gb.niH.value" class="bag-bar">
      <label>Bag Destination</label>
      <select class="field-input" style="max-width: 260px" v-model="gb.defBag.value">
        <option v-for="b in warehouses" :key="b">{{ b }}</option>
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
import { inject, ref, onMounted } from 'vue'

const gb = inject('gb')

const warehouses = ref([])

const fetchWarehouses = async () => {
  const res = await frappe.call({
    method: "frappe.client.get_list",
    args: {
      doctype: "Warehouse",
      fields: ["name"],
      filters: {
        is_group: 0   // only leaf warehouses
      },
      limit_page_length: 100
    }
  })

  warehouses.value = res.message?.map(w => w.name) || []
}

onMounted(() => {
  fetchWarehouses()
})
</script>
