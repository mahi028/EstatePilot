<script setup>
import { ref, onMounted } from 'vue'
import { fetchManagedTickets } from '@/services/dashboard'

const tickets = ref([])
const loading = ref(true)
const error = ref('')
const statusFilter = ref('')

const statuses = ['', 'open', 'assigned', 'in_progress', 'done']
const statusLabels = { '': 'All', open: 'Open', assigned: 'Assigned', in_progress: 'In Progress', done: 'Done' }
const statusColors = {
  open: 'bg-info-100 text-info-700',
  assigned: 'bg-accent-100 text-accent-700',
  in_progress: 'bg-primary-100 text-primary-700',
  done: 'bg-success-100 text-success-700',
}
const priorityColors = {
  low: 'bg-surface-100 text-surface-600',
  medium: 'bg-accent-100 text-accent-700',
  high: 'bg-danger-100 text-danger-700',
}

async function loadTickets() {
  loading.value = true
  error.value = ''
  try {
    const params = {}
    if (statusFilter.value) params.status = statusFilter.value
    const { data } = await fetchManagedTickets(params)
    tickets.value = data.tickets
  } catch {
    error.value = 'Failed to load tickets.'
  } finally {
    loading.value = false
  }
}

function onFilterChange() {
  loadTickets()
}

onMounted(loadTickets)
</script>

<template>
  <div class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-6 shadow-sm">
    <div class="mb-4 flex items-center justify-between">
      <h3 class="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
        Tenant Tickets
      </h3>
      <select
        v-model="statusFilter"
        @change="onFilterChange"
        class="rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-2 py-1 text-xs text-[var(--color-text-primary)] focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
      >
        <option v-for="s in statuses" :key="s" :value="s">{{ statusLabels[s] }}</option>
      </select>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-sm text-[var(--color-text-muted)]">Loading...</div>

    <!-- Error -->
    <div v-else-if="error" class="text-sm text-danger-500">{{ error }}</div>

    <!-- Empty -->
    <div v-else-if="tickets.length === 0" class="text-sm text-[var(--color-text-secondary)]">
      No tickets found.
    </div>

    <!-- Tickets table -->
    <div v-else class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-[var(--color-border-default)] text-left text-xs uppercase tracking-wider text-[var(--color-text-muted)]">
            <th class="pb-2 pr-4">Title</th>
            <th class="pb-2 pr-4">Tenant</th>
            <th class="pb-2 pr-4">Status</th>
            <th class="pb-2 pr-4">Priority</th>
            <th class="pb-2">Date</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-[var(--color-border-default)]">
          <tr v-for="ticket in tickets" :key="ticket.id">
            <td class="py-3 pr-4 font-medium text-[var(--color-text-primary)]">{{ ticket.title }}</td>
            <td class="py-3 pr-4 text-[var(--color-text-secondary)]">{{ ticket.created_by.name }}</td>
            <td class="py-3 pr-4">
              <span :class="statusColors[ticket.status]" class="inline-block rounded-full px-2 py-0.5 text-xs font-medium capitalize">
                {{ ticket.status.replace('_', ' ') }}
              </span>
            </td>
            <td class="py-3 pr-4">
              <span :class="priorityColors[ticket.priority]" class="inline-block rounded-full px-2 py-0.5 text-xs font-medium capitalize">
                {{ ticket.priority }}
              </span>
            </td>
            <td class="py-3 text-[var(--color-text-muted)]">
              {{ new Date(ticket.created_at).toLocaleDateString() }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
