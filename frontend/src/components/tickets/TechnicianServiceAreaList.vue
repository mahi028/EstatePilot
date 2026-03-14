<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { fetchTechnicianServiceAreaTickets } from '@/services/dashboard'

const tickets = ref([])
const filters = ref({ q: '', page: 1, page_size: 8 })
const pagination = ref({ page: 1, page_size: 8, total: 0, total_pages: 0 })
const loading = ref(true)
const error = ref('')

function statusLabel(status, pending = false) {
  if (pending) return 'Request pending'
  return String(status || '').replace('_', ' ')
}

function statusTone(status, pending = false) {
  if (pending) return 'bg-amber-100 text-amber-800 border-amber-200'
  if (status === 'open') return 'bg-sky-100 text-sky-800 border-sky-200'
  if (status === 'assigned') return 'bg-indigo-100 text-indigo-800 border-indigo-200'
  if (status === 'in_progress') return 'bg-blue-100 text-blue-800 border-blue-200'
  if (status === 'done') return 'bg-emerald-100 text-emerald-800 border-emerald-200'
  if (status === 'invalid') return 'bg-rose-100 text-rose-800 border-rose-200'
  return 'bg-slate-100 text-slate-700 border-slate-200'
}

function priorityTone(priority) {
  if (priority === 'high') return 'bg-rose-100 text-rose-700 border-rose-200'
  if (priority === 'medium') return 'bg-amber-100 text-amber-700 border-amber-200'
  if (priority === 'low') return 'bg-emerald-100 text-emerald-700 border-emerald-200'
  return 'bg-slate-100 text-slate-700 border-slate-200'
}

async function loadTickets() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await fetchTechnicianServiceAreaTickets({
      q: filters.value.q || undefined,
      page: filters.value.page,
      page_size: filters.value.page_size,
    })
    tickets.value = data.tickets || []
    pagination.value = data.pagination || { page: 1, page_size: filters.value.page_size, total: 0, total_pages: 0 }
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to load service-area tickets.'
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  filters.value.page = 1
  loadTickets()
}

function clearFilters() {
  filters.value.q = ''
  filters.value.page = 1
  loadTickets()
}

function goToPage(nextPage) {
  if (nextPage < 1 || nextPage > (pagination.value.total_pages || 1)) return
  filters.value.page = nextPage
  loadTickets()
}

onMounted(() => loadTickets())
</script>

<template>
  <div class="space-y-4">
    <article class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
      <div class="grid gap-3 sm:grid-cols-[1fr_auto_auto]">
        <input
          v-model="filters.q"
          type="text"
          placeholder="Search by title, issue, or service tag"
          class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm"
          @keyup.enter="applyFilters"
        />
        <button type="button" class="rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white" @click="applyFilters">Apply</button>
        <button type="button" class="rounded-lg border border-[var(--color-border-default)] px-3 py-2 text-xs font-semibold" @click="clearFilters">Reset</button>
      </div>
    </article>

    <div v-if="loading" class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 text-sm text-[var(--color-text-muted)]">Loading opportunities...</div>
    <div v-else-if="error" class="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{{ error }}</div>
    <div v-else-if="!tickets.length" class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-5 text-sm text-[var(--color-text-secondary)]">No open tickets available in your service area.</div>

    <div v-else class="space-y-3">
      <article
        v-for="ticket in tickets"
        :key="ticket.id"
        class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4"
      >
        <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <span class="rounded-full border px-2.5 py-1 text-xs font-semibold capitalize" :class="statusTone(ticket.status, ticket.technician_request_pending)">
                {{ statusLabel(ticket.status, ticket.technician_request_pending) }}
              </span>
              <span class="rounded-full border px-2.5 py-1 text-xs font-semibold capitalize" :class="priorityTone(ticket.priority)">
                {{ ticket.priority }} priority
              </span>
              <span class="text-xs text-[var(--color-text-muted)]">{{ new Date(ticket.created_at).toLocaleString() }}</span>
            </div>

            <h3 class="mt-2 truncate text-base font-semibold text-[var(--color-text-primary)]">{{ ticket.title }}</h3>
            <p class="mt-1 line-clamp-2 text-sm text-[var(--color-text-secondary)]">{{ ticket.description }}</p>
            <div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-[var(--color-text-muted)]">
              <span>Service: {{ ticket.service_tag?.label || 'Not set' }}</span>
              <span>Tenant: {{ ticket.created_by?.name || 'Unknown' }}</span>
            </div>
          </div>

          <RouterLink
            :to="`/tickets/${ticket.id}?scope=service-area`"
            class="inline-flex h-10 items-center justify-center rounded-lg bg-slate-900 px-4 text-sm font-semibold text-white hover:bg-slate-700"
          >
            View
          </RouterLink>
        </div>
      </article>

      <div class="flex flex-col gap-2 rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] px-3 py-2 text-xs text-[var(--color-text-secondary)] sm:flex-row sm:items-center sm:justify-between">
        <span>Page {{ pagination.page || 1 }} of {{ pagination.total_pages || 1 }} ({{ pagination.total || 0 }} total)</span>
        <div class="flex gap-2">
          <button
            type="button"
            class="rounded border border-[var(--color-border-default)] px-2 py-1 disabled:opacity-50"
            :disabled="(pagination.page || 1) <= 1"
            @click="goToPage((pagination.page || 1) - 1)"
          >Prev</button>
          <button
            type="button"
            class="rounded border border-[var(--color-border-default)] px-2 py-1 disabled:opacity-50"
            :disabled="(pagination.page || 1) >= (pagination.total_pages || 1)"
            @click="goToPage((pagination.page || 1) + 1)"
          >Next</button>
        </div>
      </div>
    </div>
  </div>
</template>
