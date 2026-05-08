<template>
  <div class="ag-contact-list-root">

    <!-- ── TOOLBAR ── -->
    <div class="ag-list-toolbar">
      <div class="ag-list-search-wrap">
        <input
          type="text"
          class="ag-list-search"
          placeholder="Search by name, phone or ID…"
          v-model="searchTxt"
          @input="onSearchInput"
        />
        <span v-if="loading" class="ag-list-spinner">⟳</span>
      </div>
      <button class="ag-list-new-btn" @click="openNew">+ New Contact</button>
    </div>

    <!-- ── TABLE ── -->
    <div class="ag-list-table-wrap">
      <table class="ag-list-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Full Name</th>
            <th>Entity</th>
            <th>ID Type / Number</th>
            <th>Phone</th>
            <th>Linked Customer</th>
            <th>Active</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading && !contacts.length">
            <td colspan="8" class="ag-list-empty">Loading…</td>
          </tr>
          <tr v-else-if="!loading && !contacts.length">
            <td colspan="8" class="ag-list-empty">No contacts found.</td>
          </tr>
          <tr
            v-for="c in contacts"
            :key="c.name"
            class="ag-list-row"
            @click="openContact(c.name)"
          >
            <td class="ag-list-id">{{ c.name }}</td>
            <td class="ag-list-name">{{ c.display_name }}</td>
            <td>{{ c.entity_type || '—' }}</td>
            <td class="ag-list-id-col">
              <span class="ag-id-badge">{{ idLabel(c) }}</span>
              {{ c.id_number || '—' }}
            </td>
            <td>{{ c.phone_primary || '—' }}</td>
            <td>
              <span v-if="c.linked_customer" class="ag-linked-badge">{{ c.linked_customer }}</span>
              <span v-else class="ag-unlinked-badge">—</span>
            </td>
            <td>
              <span :class="c.is_active ? 'ag-active-dot' : 'ag-inactive-dot'">
                {{ c.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td class="ag-list-actions" @click.stop>
              <a :href="contactUrl(c.name)" target="_blank" class="ag-action-link">Open ↗</a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── PAGINATION ── -->
    <div v-if="hasMore || page > 0" class="ag-list-pagination">
      <button class="ag-page-btn" :disabled="page === 0" @click="prevPage">← Prev</button>
      <span class="ag-page-info">Page {{ page + 1 }}</span>
      <button class="ag-page-btn" :disabled="!hasMore" @click="nextPage">Next →</button>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const PAGE_SIZE = 20

const contacts   = ref([])
const loading    = ref(false)
const searchTxt  = ref('')
const page       = ref(0)
const hasMore    = ref(false)
let   debounceTimer = null

// ── Fetch ──────────────────────────────────────────────────────────────────

const fetchContacts = async () => {
  loading.value = true
  try {
    const res = await frappe.call({
      method: 'anygold_custom.api.ag_contact.list_ag_contacts',
      args: {
        txt:    searchTxt.value.trim(),
        limit:  PAGE_SIZE + 1,
        offset: page.value * PAGE_SIZE,
      },
    })
    const rows = res.message || []
    hasMore.value    = rows.length > PAGE_SIZE
    contacts.value   = rows.slice(0, PAGE_SIZE)
  } catch (e) {
    console.warn('AG Contact list fetch failed', e)
    contacts.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchContacts)

// ── Search ─────────────────────────────────────────────────────────────────

const onSearchInput = () => {
  page.value = 0
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchContacts, 280)
}

// ── Pagination ─────────────────────────────────────────────────────────────

const prevPage = () => { page.value--; fetchContacts() }
const nextPage = () => { page.value++; fetchContacts() }

// ── Navigation ─────────────────────────────────────────────────────────────

const contactUrl = (name) => `/app/ag-contact/${encodeURIComponent(name)}`

const openContact = (name) => frappe.set_route('Form', 'AG Contact', name)

const openNew = () => frappe.new_doc('AG Contact')

// ── Helpers ────────────────────────────────────────────────────────────────

const idLabel = (c) =>
  c.id_type === 'Malaysian IC' ? 'IC'
  : c.id_type === 'Passport'   ? 'PP'
  : c.id_type === 'SSM Number' ? 'SSM'
  : c.id_type || 'ID'
</script>

<style scoped>
.ag-contact-list-root {
  padding: 20px;
  font-family: var(--font-stack);
  color: var(--text-color);
}

/* ── Toolbar ── */
.ag-list-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.ag-list-search-wrap {
  position: relative;
  flex: 1;
  max-width: 400px;
}
.ag-list-search {
  width: 100%;
  padding: 7px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 13px;
  background: var(--card-bg);
  color: var(--text-color);
  outline: none;
}
.ag-list-search:focus { border-color: var(--primary-color, #d4a843); }
.ag-list-spinner {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 14px;
  animation: ag-spin 0.8s linear infinite;
  display: inline-block;
}
@keyframes ag-spin { to { transform: translateY(-50%) rotate(360deg); } }

.ag-list-new-btn {
  padding: 7px 16px;
  background: #c59a2f;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}
.ag-list-new-btn:hover { background: #b8891f; }

/* ── Table ── */
.ag-list-table-wrap {
  overflow-x: auto;
  border: 1px solid var(--border-color);
  border-radius: 8px;
}
.ag-list-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.ag-list-table thead th {
  background: var(--subtle-fg, #f4f4f4);
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-color);
  white-space: nowrap;
}
.ag-list-row {
  cursor: pointer;
  transition: background 0.12s;
  border-bottom: 1px solid var(--border-color);
}
.ag-list-row:last-child { border-bottom: none; }
.ag-list-row:hover { background: var(--fg-hover-color, #fafaf8); }
.ag-list-row td { padding: 10px 12px; vertical-align: middle; }

.ag-list-id    { font-family: monospace; font-size: 12px; color: var(--text-muted); }
.ag-list-name  { font-weight: 600; }
.ag-list-id-col { white-space: nowrap; }
.ag-id-badge {
  display: inline-block;
  background: #f0e8d0;
  color: #8a6a10;
  border-radius: 3px;
  padding: 1px 5px;
  font-size: 10px;
  font-weight: 700;
  margin-right: 4px;
}
.ag-linked-badge {
  font-family: monospace;
  font-size: 11px;
  color: var(--text-muted);
}
.ag-unlinked-badge { color: var(--text-subtle); }
.ag-active-dot   { color: var(--green, #4caf50); font-weight: 600; font-size: 12px; }
.ag-inactive-dot { color: var(--text-muted);     font-size: 12px; }

.ag-list-actions { text-align: right; white-space: nowrap; }
.ag-action-link {
  font-size: 11px;
  color: var(--text-muted);
  text-decoration: none;
}
.ag-action-link:hover { color: var(--primary-color, #c59a2f); }

.ag-list-empty {
  text-align: center;
  padding: 32px;
  color: var(--text-muted);
  font-size: 13px;
}

/* ── Pagination ── */
.ag-list-pagination {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 14px;
  justify-content: flex-end;
}
.ag-page-btn {
  padding: 5px 14px;
  border: 1px solid var(--border-color);
  border-radius: 5px;
  background: var(--card-bg);
  font-size: 12px;
  cursor: pointer;
  color: var(--text-color);
}
.ag-page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.ag-page-info { font-size: 12px; color: var(--text-muted); }
</style>
