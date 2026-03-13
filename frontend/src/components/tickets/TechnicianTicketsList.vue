<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { fetchTechnicianServiceAreaTickets, fetchTechnicianTickets } from '@/services/dashboard'

const serviceAreaTickets = ref([])
const assignedTickets = ref([])
const serviceAreaFilters = ref({ q: '', page: 1, page_size: 6 })
const assignedFilters = ref({ q: '', status: '', page: 1, page_size: 6 })
const serviceAreaPagination = ref({ page: 1, page_size: 6, total: 0, total_pages: 0 })
const assignedPagination = ref({ page: 1, page_size: 6, total: 0, total_pages: 0 })
const loadingServiceArea = ref(true)
const loadingAssigned = ref(true)
const errorServiceArea = ref('')
const errorAssigned = ref('')

async function loadServiceArea() {
  loadingServiceArea.value = true
  errorServiceArea.value = ''
  try {
    const { data } = await fetchTechnicianServiceAreaTickets({
      q: serviceAreaFilters.value.q || undefined,
      page: serviceAreaFilters.value.page,
      page_size: serviceAreaFilters.value.page_size,
    })
    serviceAreaTickets.value = data.tickets || []
    serviceAreaPagination.value = data.pagination || { page: 1, page_size: serviceAreaFilters.value.page_size, total: 0, total_pages: 0 }
  } catch (err) {
    errorServiceArea.value = err.response?.data?.message || 'Failed to load service-area tickets.'
  } finally {
    loadingServiceArea.value = false
  }
}

async function loadAssigned() {
  loadingAssigned.value = true
  errorAssigned.value = ''
  try {
    const { data } = await fetchTechnicianTickets({
      q: assignedFilters.value.q || undefined,
      status: assignedFilters.value.status || undefined,
      page: assignedFilters.value.page,
      page_size: assignedFilters.value.page_size,
    })
    assignedTickets.value = data.tickets || []
    assignedPagination.value = data.pagination || { page: 1, page_size: assignedFilters.value.page_size, total: 0, total_pages: 0 }
  } catch (err) {
    errorAssigned.value = err.response?.data?.message || 'Failed to load assigned tickets.'
  } finally {
    loadingAssigned.value = false
  }
}

function applyServiceAreaFilters() {
  serviceAreaFilters.value.page = 1
  loadServiceArea()
}

function applyAssignedFilters() {
  assignedFilters.value.page = 1
  loadAssigned()
}

function goServiceAreaPage(nextPage) {
  if (nextPage < 1 || nextPage > (serviceAreaPagination.value.total_pages || 1)) return
  serviceAreaFilters.value.page = nextPage
  loadServiceArea()
}

function goAssignedPage(nextPage) {
  if (nextPage < 1 || nextPage > (assignedPagination.value.total_pages || 1)) return
  assignedFilters.value.page = nextPage
  loadAssigned()
}

onMounted(async () => {
  await Promise.all([loadServiceArea(), loadAssigned()])
})
</script>

<template>
  <div class="space-y-5">
    <section>
      <h2 class="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Service-area tickets</h2>
      <div class="mt-2 grid gap-2 sm:grid-cols-[1fr_auto]">
        <input
          v-model="serviceAreaFilters.q"
          type="text"
          placeholder="Search open tickets"
          class="h-10 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm"
          @keyup.enter="applyServiceAreaFilters"
        />
        <button type="button" class="rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white" @click="applyServiceAreaFilters">Search</button>
      </div>
      <div v-if="loadingServiceArea" class="mt-2 text-sm text-[var(--color-text-muted)]">Loading...</div>
      <div v-else-if="errorServiceArea" class="mt-2 text-sm text-danger-500">{{ errorServiceArea }}</div>
      <div v-else-if="!serviceAreaTickets.length" class="mt-2 text-sm text-[var(--color-text-secondary)]">No open tickets to bid.</div>
      <div v-else class="mt-2 space-y-3">
        <article v-for="ticket in serviceAreaTickets" :key="ticket.id" class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
          <p class="text-xs text-[var(--color-text-secondary)]">{{ ticket.service_tag?.label || 'Service' }}</p>
          <h3 class="mt-1 text-base font-semibold text-[var(--color-text-primary)]">{{ ticket.title }}</h3>
          <p class="mt-1 line-clamp-2 text-sm text-[var(--color-text-secondary)]">{{ ticket.description }}</p>
          <div class="mt-3 flex justify-end">
            <RouterLink :to="`/tickets/${ticket.id}?scope=service-area`" class="rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-700">View</RouterLink>
          </div>
        </article>

        <div class="flex items-center justify-between rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] px-3 py-2 text-xs text-[var(--color-text-secondary)]">
          <span>Page {{ serviceAreaPagination.page || 1 }} of {{ serviceAreaPagination.total_pages || 1 }}</span>
          <div class="flex gap-2">
            <button type="button" class="rounded border border-[var(--color-border-default)] px-2 py-1 disabled:opacity-50" :disabled="(serviceAreaPagination.page || 1) <= 1" @click="goServiceAreaPage((serviceAreaPagination.page || 1) - 1)">Prev</button>
            <button type="button" class="rounded border border-[var(--color-border-default)] px-2 py-1 disabled:opacity-50" :disabled="(serviceAreaPagination.page || 1) >= (serviceAreaPagination.total_pages || 1)" @click="goServiceAreaPage((serviceAreaPagination.page || 1) + 1)">Next</button>
          </div>
        </div>
      </div>
    </section>

    <section>
      <h2 class="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--color-text-muted)]">My ticket requests</h2>
      <div class="mt-2 grid gap-2 sm:grid-cols-[1fr_160px_auto]">
        <input
          v-model="assignedFilters.q"
          type="text"
          placeholder="Search assigned tickets"
          class="h-10 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm"
          @keyup.enter="applyAssignedFilters"
        />
        <select v-model="assignedFilters.status" class="h-10 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm">
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="assigned">Assigned</option>
          <option value="in_progress">In progress</option>
          <option value="done">Done</option>
          <option value="invalid">Invalid</option>
        </select>
        <button type="button" class="rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white" @click="applyAssignedFilters">Apply</button>
      </div>
      <div v-if="loadingAssigned" class="mt-2 text-sm text-[var(--color-text-muted)]">Loading...</div>
      <div v-else-if="errorAssigned" class="mt-2 text-sm text-danger-500">{{ errorAssigned }}</div>
      <div v-else-if="!assignedTickets.length" class="mt-2 text-sm text-[var(--color-text-secondary)]">No assigned/requested tickets.</div>
      <div v-else class="mt-2 space-y-3">
        <article v-for="ticket in assignedTickets" :key="ticket.id" class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
          <p class="text-xs text-[var(--color-text-secondary)]">{{ ticket.technician_request_pending ? 'request pending' : ticket.status.replace('_', ' ') }}</p>
          <h3 class="mt-1 text-base font-semibold text-[var(--color-text-primary)]">{{ ticket.title }}</h3>
          <p class="mt-1 line-clamp-2 text-sm text-[var(--color-text-secondary)]">{{ ticket.description }}</p>
          <div class="mt-3 flex justify-end">
            <RouterLink :to="`/tickets/${ticket.id}`" class="rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-700">Open</RouterLink>
          </div>
        </article>

        <div class="flex items-center justify-between rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] px-3 py-2 text-xs text-[var(--color-text-secondary)]">
          <span>Page {{ assignedPagination.page || 1 }} of {{ assignedPagination.total_pages || 1 }}</span>
          <div class="flex gap-2">
            <button type="button" class="rounded border border-[var(--color-border-default)] px-2 py-1 disabled:opacity-50" :disabled="(assignedPagination.page || 1) <= 1" @click="goAssignedPage((assignedPagination.page || 1) - 1)">Prev</button>
            <button type="button" class="rounded border border-[var(--color-border-default)] px-2 py-1 disabled:opacity-50" :disabled="(assignedPagination.page || 1) >= (assignedPagination.total_pages || 1)" @click="goAssignedPage((assignedPagination.page || 1) + 1)">Next</button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
