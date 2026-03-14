<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { fetchTechnicianTickets } from '@/services/dashboard'

const assignedTickets = ref([])

const assignedFilters = ref({ q: '', status: '', priority: '', page: 1, page_size: 8 })

const assignedPagination = ref({ page: 1, page_size: 8, total: 0, total_pages: 0 })

const loadingAssigned = ref(true)
const errorAssigned = ref('')

const assignedStatusOptions = ['assigned', 'in_progress', 'done', 'invalid']
const assignedPriorityOptions = ['low', 'medium', 'high']

const assignedStatusSummary = ref({ assigned: 0, in_progress: 0, done: 0, invalid: 0 })
const assignedPrioritySummary = ref({ low: 0, medium: 0, high: 0 })
const assignedSummaryQuery = ref('')

function statusLabel(status, pending = false) {
  if (pending) return 'Request pending'
  return String(status || '').replace('_', ' ')
}

function statusTone(status, pending = false) {
  if (pending) return 'bg-amber-100 text-amber-800 border-amber-200'
  if (status === 'assigned') return 'bg-indigo-100 text-indigo-800 border-indigo-200'
  if (status === 'in_progress') return 'bg-blue-100 text-blue-800 border-blue-200'
  if (status === 'done') return 'bg-emerald-100 text-emerald-800 border-emerald-200'
  if (status === 'invalid') return 'bg-rose-100 text-rose-800 border-rose-200'
  if (status === 'open') return 'bg-sky-100 text-sky-800 border-sky-200'
  return 'bg-slate-100 text-slate-700 border-slate-200'
}

function priorityTone(priority) {
  if (priority === 'high') return 'bg-rose-100 text-rose-700 border-rose-200'
  if (priority === 'medium') return 'bg-amber-100 text-amber-700 border-amber-200'
  if (priority === 'low') return 'bg-emerald-100 text-emerald-700 border-emerald-200'
  return 'bg-slate-100 text-slate-700 border-slate-200'
}

function recalculateAssignedSummaryCounts(sourceTickets) {
  const nextStatus = { assigned: 0, in_progress: 0, done: 0, invalid: 0 }
  const nextPriority = { low: 0, medium: 0, high: 0 }
  for (const ticket of sourceTickets) {
    const s = ticket.technician_request_pending ? 'assigned' : ticket.status
    if (nextStatus[s] != null) nextStatus[s] += 1
    if (nextPriority[ticket.priority] != null) nextPriority[ticket.priority] += 1
  }
  assignedStatusSummary.value = nextStatus
  assignedPrioritySummary.value = nextPriority
}

async function loadAssignedSummaryCounts(force = false) {
  const q = (assignedFilters.value.q || '').trim()
  if (!force && assignedSummaryQuery.value === q) return
  assignedSummaryQuery.value = q
  const collected = []
  let page = 1
  let totalPages = 1
  do {
    const { data } = await fetchTechnicianTickets({ q: q || undefined, page, page_size: 50 })
    collected.push(...(data.tickets || []))
    totalPages = data.pagination?.total_pages || 1
    page += 1
  } while (page <= totalPages)
  recalculateAssignedSummaryCounts(collected)
}

async function loadAssigned(forceSummary = false) {
  loadingAssigned.value = true
  errorAssigned.value = ''
  try {
    const { data } = await fetchTechnicianTickets({
      q: assignedFilters.value.q || undefined,
      status: assignedFilters.value.status || undefined,
      priority: assignedFilters.value.priority || undefined,
      page: assignedFilters.value.page,
      page_size: assignedFilters.value.page_size,
    })
    assignedTickets.value = data.tickets || []
    assignedPagination.value = data.pagination || { page: 1, page_size: assignedFilters.value.page_size, total: 0, total_pages: 0 }
    await loadAssignedSummaryCounts(forceSummary)
  } catch (err) {
    errorAssigned.value = err.response?.data?.message || 'Failed to load assigned tickets.'
  } finally {
    loadingAssigned.value = false
  }
}

function applyAssignedFilters() {
  assignedFilters.value.page = 1
  loadAssigned()
}

function clearAssignedFilters() {
  assignedFilters.value.q = ''
  assignedFilters.value.status = ''
  assignedFilters.value.priority = ''
  assignedFilters.value.page = 1
  loadAssigned()
}

function setAssignedStatus(status) {
  assignedFilters.value.status = assignedFilters.value.status === status ? '' : status
  assignedFilters.value.page = 1
  loadAssigned()
}

function setAssignedPriority(priority) {
  assignedFilters.value.priority = assignedFilters.value.priority === priority ? '' : priority
  assignedFilters.value.page = 1
  loadAssigned()
}

function goAssignedPage(nextPage) {
  if (nextPage < 1 || nextPage > (assignedPagination.value.total_pages || 1)) return
  assignedFilters.value.page = nextPage
  loadAssigned()
}

onMounted(() => loadAssigned(true))
</script>

<template>
  <div class="space-y-4">
      <div class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
        <h2 class="text-base font-semibold text-[var(--color-text-primary)]">My active requests</h2>
        <p class="mt-1 text-sm text-[var(--color-text-secondary)]">Track assigned work, progress updates, and completed jobs.</p>

        <div class="mt-4 grid gap-3 sm:grid-cols-[1fr_auto_auto]">
          <input
            v-model="assignedFilters.q"
            type="text"
            placeholder="Search assigned tickets"
            class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm"
            @keyup.enter="applyAssignedFilters"
          />
          <div class="flex gap-2">
            <button type="button" class="rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white" @click="applyAssignedFilters">Apply</button>
            <button type="button" class="rounded-lg border border-[var(--color-border-default)] px-3 py-2 text-xs font-semibold" @click="clearAssignedFilters">Reset</button>
          </div>
        </div>
      </div>

      <article class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-3">
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">Status totals</span>
          <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[statusTone('assigned'), assignedFilters.status === 'assigned' ? 'ring-1 ring-offset-1 ring-indigo-300' : 'opacity-75 hover:opacity-100']" @click="setAssignedStatus('assigned')">Assigned {{ assignedStatusSummary.assigned }}</button>
          <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[statusTone('in_progress'), assignedFilters.status === 'in_progress' ? 'ring-1 ring-offset-1 ring-blue-300' : 'opacity-75 hover:opacity-100']" @click="setAssignedStatus('in_progress')">In Progress {{ assignedStatusSummary.in_progress }}</button>
          <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[statusTone('done'), assignedFilters.status === 'done' ? 'ring-1 ring-offset-1 ring-emerald-300' : 'opacity-75 hover:opacity-100']" @click="setAssignedStatus('done')">Done {{ assignedStatusSummary.done }}</button>
          <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[statusTone('invalid'), assignedFilters.status === 'invalid' ? 'ring-1 ring-offset-1 ring-rose-300' : 'opacity-75 hover:opacity-100']" @click="setAssignedStatus('invalid')">Invalid {{ assignedStatusSummary.invalid }}</button>
        </div>
        <div class="mt-2 flex flex-wrap items-center gap-2">
          <span class="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">Priority totals</span>
          <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[priorityTone('low'), assignedFilters.priority === 'low' ? 'ring-1 ring-offset-1 ring-emerald-300' : 'opacity-75 hover:opacity-100']" @click="setAssignedPriority('low')">Low {{ assignedPrioritySummary.low }}</button>
          <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[priorityTone('medium'), assignedFilters.priority === 'medium' ? 'ring-1 ring-offset-1 ring-amber-300' : 'opacity-75 hover:opacity-100']" @click="setAssignedPriority('medium')">Medium {{ assignedPrioritySummary.medium }}</button>
          <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[priorityTone('high'), assignedFilters.priority === 'high' ? 'ring-1 ring-offset-1 ring-rose-300' : 'opacity-75 hover:opacity-100']" @click="setAssignedPriority('high')">High {{ assignedPrioritySummary.high }}</button>
        </div>
      </article>

      <div v-if="loadingAssigned" class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 text-sm text-[var(--color-text-muted)]">Loading assigned tickets...</div>
      <div v-else-if="errorAssigned" class="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{{ errorAssigned }}</div>
      <div v-else-if="!assignedTickets.length" class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-5 text-sm text-[var(--color-text-secondary)]">No assigned or requested tickets yet.</div>

      <div v-else class="space-y-3">
        <article v-for="ticket in assignedTickets" :key="ticket.id" class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
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

            <RouterLink :to="`/tickets/${ticket.id}`" class="inline-flex h-10 items-center justify-center rounded-lg bg-slate-900 px-4 text-sm font-semibold text-white hover:bg-slate-700">
              Open
            </RouterLink>
          </div>
        </article>

        <div class="flex flex-col gap-2 rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] px-3 py-2 text-xs text-[var(--color-text-secondary)] sm:flex-row sm:items-center sm:justify-between">
          <span>Page {{ assignedPagination.page || 1 }} of {{ assignedPagination.total_pages || 1 }} ({{ assignedPagination.total || 0 }} total)</span>
          <div class="flex gap-2">
            <button type="button" class="rounded border border-[var(--color-border-default)] px-2 py-1 disabled:opacity-50" :disabled="(assignedPagination.page || 1) <= 1" @click="goAssignedPage((assignedPagination.page || 1) - 1)">Prev</button>
            <button type="button" class="rounded border border-[var(--color-border-default)] px-2 py-1 disabled:opacity-50" :disabled="(assignedPagination.page || 1) >= (assignedPagination.total_pages || 1)" @click="goAssignedPage((assignedPagination.page || 1) + 1)">Next</button>
          </div>
        </div>
      </div>
  </div>
</template>
