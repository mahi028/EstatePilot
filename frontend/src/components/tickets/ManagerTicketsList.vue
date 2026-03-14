<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { fetchManagedTickets } from '@/services/dashboard'

const tickets = ref([])
const filters = ref({ q: '', status: '', priority: '', page: 1, page_size: 8 })
const pagination = ref({ page: 1, page_size: 8, total: 0, total_pages: 0 })
const loading = ref(true)
const error = ref('')

const statusOptions = ['open', 'assigned', 'in_progress', 'done', 'invalid']
const priorityOptions = ['low', 'medium', 'high']

const statusSummary = ref({ open: 0, assigned: 0, in_progress: 0, done: 0, invalid: 0 })
const prioritySummary = ref({ low: 0, medium: 0, high: 0 })
const summaryQuery = ref('')

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

function recalculateSummaryCounts(sourceTickets) {
  const nextStatus = { open: 0, assigned: 0, in_progress: 0, done: 0, invalid: 0 }
  const nextPriority = { low: 0, medium: 0, high: 0 }

  for (const ticket of sourceTickets) {
    if (nextStatus[ticket.status] != null) nextStatus[ticket.status] += 1
    if (nextPriority[ticket.priority] != null) nextPriority[ticket.priority] += 1
  }

  statusSummary.value = nextStatus
  prioritySummary.value = nextPriority
}

async function loadSummaryCounts(force = false) {
  const q = (filters.value.q || '').trim()
  if (!force && summaryQuery.value === q) return

  summaryQuery.value = q
  const collected = []
  let page = 1
  let totalPages = 1

  do {
    const { data } = await fetchManagedTickets({
      q: q || undefined,
      page,
      page_size: 50,
    })
    const pageTickets = data.tickets || []
    collected.push(...pageTickets)
    totalPages = data.pagination?.total_pages || 1
    page += 1
  } while (page <= totalPages)

  recalculateSummaryCounts(collected)
}

async function loadTickets(forceSummary = false) {
  loading.value = true
  error.value = ''
  try {
    const { data } = await fetchManagedTickets({
      q: filters.value.q || undefined,
      status: filters.value.status || undefined,
      priority: filters.value.priority || undefined,
      page: filters.value.page,
      page_size: filters.value.page_size,
    })
    tickets.value = data.tickets || []
    pagination.value = data.pagination || { page: 1, page_size: filters.value.page_size, total: 0, total_pages: 0 }
    await loadSummaryCounts(forceSummary)
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to load tickets.'
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
  filters.value.status = ''
  filters.value.priority = ''
  filters.value.page = 1
  loadTickets()
}

function setStatusFilter(status) {
  filters.value.status = filters.value.status === status ? '' : status
  filters.value.page = 1
  loadTickets()
}

function setPriorityFilter(priority) {
  filters.value.priority = filters.value.priority === priority ? '' : priority
  filters.value.page = 1
  loadTickets()
}

function goToPage(nextPage) {
  if (nextPage < 1 || nextPage > (pagination.value.total_pages || 1)) return
  filters.value.page = nextPage
  loadTickets()
}

onMounted(() => loadTickets(true))
</script>

<template>
  <div class="space-y-4">
    <article class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
      <h2 class="text-base font-semibold text-[var(--color-text-primary)]">Managed workflow queue</h2>
      <p class="mt-1 text-sm text-[var(--color-text-secondary)]">Prioritize, assign, and drive ticket completion across all managed tenants.</p>

      <div class="mt-4 grid gap-3 sm:grid-cols-[1fr_auto_auto]">
        <input
          v-model="filters.q"
          type="text"
          placeholder="Search title, description, or tenant"
          class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm"
          @keyup.enter="applyFilters"
        />
        <div class="flex gap-2">
          <button type="button" class="rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white" @click="applyFilters">Apply</button>
          <button type="button" class="rounded-lg border border-[var(--color-border-default)] px-3 py-2 text-xs font-semibold" @click="clearFilters">Reset</button>
        </div>
      </div>

    </article>

    <article class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-3">
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">Status totals</span>
        <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[statusTone('open'), filters.status === 'open' ? 'ring-1 ring-offset-1 ring-sky-300' : 'opacity-75 hover:opacity-100']" @click="setStatusFilter('open')">Open {{ statusSummary.open }}</button>
        <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[statusTone('assigned'), filters.status === 'assigned' ? 'ring-1 ring-offset-1 ring-indigo-300' : 'opacity-75 hover:opacity-100']" @click="setStatusFilter('assigned')">Assigned {{ statusSummary.assigned }}</button>
        <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[statusTone('in_progress'), filters.status === 'in_progress' ? 'ring-1 ring-offset-1 ring-blue-300' : 'opacity-75 hover:opacity-100']" @click="setStatusFilter('in_progress')">In Progress {{ statusSummary.in_progress }}</button>
        <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[statusTone('done'), filters.status === 'done' ? 'ring-1 ring-offset-1 ring-emerald-300' : 'opacity-75 hover:opacity-100']" @click="setStatusFilter('done')">Done {{ statusSummary.done }}</button>
        <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[statusTone('invalid'), filters.status === 'invalid' ? 'ring-1 ring-offset-1 ring-rose-300' : 'opacity-75 hover:opacity-100']" @click="setStatusFilter('invalid')">Invalid {{ statusSummary.invalid }}</button>
      </div>
      <div class="mt-2 flex flex-wrap items-center gap-2">
        <span class="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">Priority totals</span>
        <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[priorityTone('low'), filters.priority === 'low' ? 'ring-1 ring-offset-1 ring-emerald-300' : 'opacity-75 hover:opacity-100']" @click="setPriorityFilter('low')">Low {{ prioritySummary.low }}</button>
        <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[priorityTone('medium'), filters.priority === 'medium' ? 'ring-1 ring-offset-1 ring-amber-300' : 'opacity-75 hover:opacity-100']" @click="setPriorityFilter('medium')">Medium {{ prioritySummary.medium }}</button>
        <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[priorityTone('high'), filters.priority === 'high' ? 'ring-1 ring-offset-1 ring-rose-300' : 'opacity-75 hover:opacity-100']" @click="setPriorityFilter('high')">High {{ prioritySummary.high }}</button>
      </div>
    </article>

    <div v-if="loading" class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 text-sm text-[var(--color-text-muted)]">Loading tickets...</div>
    <div v-else-if="error" class="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{{ error }}</div>
    <div v-else-if="!tickets.length" class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-5 text-sm text-[var(--color-text-secondary)]">No tickets match your filters.</div>

    <div v-else class="space-y-3">
      <article v-for="ticket in tickets" :key="ticket.id" class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
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
              <span>Tenant: {{ ticket.created_by?.name || 'Unknown' }}</span>
              <span>Technician: {{ ticket.assigned_to?.name || 'Unassigned' }}</span>
              <span>Service: {{ ticket.service_tag?.label || 'Not set' }}</span>
            </div>
          </div>

          <RouterLink :to="`/tickets/${ticket.id}`" class="inline-flex h-10 items-center justify-center rounded-lg bg-slate-900 px-4 text-sm font-semibold text-white hover:bg-slate-700">
            Open
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
          >
            Prev
          </button>
          <button
            type="button"
            class="rounded border border-[var(--color-border-default)] px-2 py-1 disabled:opacity-50"
            :disabled="(pagination.page || 1) >= (pagination.total_pages || 1)"
            @click="goToPage((pagination.page || 1) + 1)"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
