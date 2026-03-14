<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { createTicket, fetchTechnicianServices, fetchTenantTickets } from '@/services/dashboard'

const auth = useAuthStore()
const router = useRouter()

const hasManager = computed(() => Boolean(auth.user?.manager_id))

const tickets = ref([])
const pagination = ref({ page: 1, page_size: 10, total: 0, total_pages: 0 })
const loading = ref(true)
const error = ref('')
const services = ref([])
const showCreateForm = ref(false)
const creating = ref(false)
const createError = ref('')
const selectedImages = ref([])

const statusOptions = ['open', 'assigned', 'in_progress', 'done', 'invalid']
const priorityOptions = ['low', 'medium', 'high']

const listFilters = ref({
  q: '',
  status: '',
  priority: '',
  page: 1,
  page_size: 8,
})

const form = ref({
  title: '',
  description: '',
  priority: 'medium',
  service_tag_id: '',
})

const canCreate = computed(() => {
  return Boolean(
    hasManager.value
      && form.value.service_tag_id
      && form.value.title.trim().length >= 5
      && form.value.description.trim().length >= 10,
  )
})

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
  const q = (listFilters.value.q || '').trim()
  if (!force && summaryQuery.value === q) return

  summaryQuery.value = q
  const collected = []
  let page = 1
  let totalPages = 1

  do {
    const { data } = await fetchTenantTickets({
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
    const { data } = await fetchTenantTickets({
      q: listFilters.value.q || undefined,
      status: listFilters.value.status || undefined,
      priority: listFilters.value.priority || undefined,
      page: listFilters.value.page,
      page_size: listFilters.value.page_size,
    })
    tickets.value = data.tickets || []
    pagination.value = data.pagination || { page: 1, page_size: listFilters.value.page_size, total: 0, total_pages: 0 }
    await loadSummaryCounts(forceSummary)
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to load tickets.'
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  listFilters.value.page = 1
  loadTickets()
}

function clearFilters() {
  listFilters.value.q = ''
  listFilters.value.status = ''
  listFilters.value.priority = ''
  listFilters.value.page = 1
  loadTickets()
}

function setStatusFilter(status) {
  listFilters.value.status = listFilters.value.status === status ? '' : status
  listFilters.value.page = 1
  loadTickets()
}

function setPriorityFilter(priority) {
  listFilters.value.priority = listFilters.value.priority === priority ? '' : priority
  listFilters.value.page = 1
  loadTickets()
}

function goToPage(nextPage) {
  if (nextPage < 1 || nextPage > (pagination.value.total_pages || 1)) return
  listFilters.value.page = nextPage
  loadTickets()
}

async function loadServices() {
  try {
    const { data } = await fetchTechnicianServices()
    services.value = data.services || []
    if (!form.value.service_tag_id && services.value.length) {
      form.value.service_tag_id = services.value[0].id
    }
  } catch {
    services.value = []
  }
}

function resetForm() {
  form.value.title = ''
  form.value.description = ''
  form.value.priority = 'medium'
  form.value.service_tag_id = services.value[0]?.id || ''
  selectedImages.value = []
}

function onCreateImagesSelected(event) {
  const files = Array.from(event.target.files || [])
  selectedImages.value = files
}

function removeCreateImageAt(index) {
  selectedImages.value = selectedImages.value.filter((_, i) => i !== index)
}

async function handleCreate() {
  if (!canCreate.value) return
  creating.value = true
  createError.value = ''
  try {
    const { data } = await createTicket({
      title: form.value.title.trim(),
      description: form.value.description.trim(),
      priority: form.value.priority,
      service_tag_id: form.value.service_tag_id,
    }, selectedImages.value)
    await loadTickets(true)
    resetForm()
    showCreateForm.value = false
    router.push(`/tickets/${data.ticket.id}`)
  } catch (err) {
    createError.value = err.response?.data?.message || err.response?.data?.errors?.title?.[0] || 'Failed to create ticket.'
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadTickets(true), loadServices()])
})
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col gap-3 rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-base font-semibold text-[var(--color-text-primary)]">My tickets</h2>
        <p class="text-sm text-[var(--color-text-secondary)]">Track every request with clear status and ownership.</p>
      </div>

      <button
        v-if="hasManager"
        type="button"
        class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
        @click="showCreateForm = !showCreateForm"
      >
        {{ showCreateForm ? 'Cancel' : 'Create ticket' }}
      </button>
    </div>

    <article v-if="!hasManager" class="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
      You need an assigned manager before you can create tickets.
    </article>

    <article v-if="showCreateForm && hasManager" class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
      <div class="grid gap-3">
        <input
          v-model="form.title"
          type="text"
          placeholder="Ticket title"
          class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm"
        />
        <textarea
          v-model="form.description"
          rows="4"
          placeholder="Describe the issue"
          class="rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] p-3 text-sm"
        ></textarea>
        <div class="grid gap-3 sm:grid-cols-2">
          <select
            v-model="form.service_tag_id"
            class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm"
          >
            <option disabled value="">Select service tag</option>
            <option v-for="service in services" :key="service.id" :value="service.id">
              {{ service.label }}
            </option>
          </select>
          <select
            v-model="form.priority"
            class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
        <div class="space-y-2">
          <label class="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">Images (optional)</label>
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            multiple
            class="block w-full cursor-pointer rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 py-2 text-sm"
            @change="onCreateImagesSelected"
          />
          <div v-if="selectedImages.length" class="flex flex-wrap gap-2">
            <span
              v-for="(file, idx) in selectedImages"
              :key="`${file.name}-${idx}`"
              class="inline-flex items-center gap-1 rounded-full border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] px-2.5 py-1 text-xs"
            >
              {{ file.name }}
              <button type="button" class="text-rose-600 hover:text-rose-700" @click="removeCreateImageAt(idx)">x</button>
            </span>
          </div>
        </div>
        <p v-if="createError" class="text-sm text-rose-700">{{ createError }}</p>
        <div class="flex justify-end">
          <button
            type="button"
            class="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-60"
            :disabled="creating || !canCreate"
            @click="handleCreate"
          >
            {{ creating ? 'Creating...' : 'Create ticket' }}
          </button>
        </div>
      </div>
    </article>

    <article class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
      <div class="mt-4 grid gap-3 sm:grid-cols-[1fr_auto_auto]">
        <input
          v-model="listFilters.q"
          type="text"
          placeholder="Search title or description"
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
        <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[statusTone('open'), listFilters.status === 'open' ? 'ring-1 ring-offset-1 ring-sky-300' : 'opacity-75 hover:opacity-100']" @click="setStatusFilter('open')">Open {{ statusSummary.open }}</button>
        <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[statusTone('assigned'), listFilters.status === 'assigned' ? 'ring-1 ring-offset-1 ring-indigo-300' : 'opacity-75 hover:opacity-100']" @click="setStatusFilter('assigned')">Assigned {{ statusSummary.assigned }}</button>
        <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[statusTone('in_progress'), listFilters.status === 'in_progress' ? 'ring-1 ring-offset-1 ring-blue-300' : 'opacity-75 hover:opacity-100']" @click="setStatusFilter('in_progress')">In Progress {{ statusSummary.in_progress }}</button>
        <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[statusTone('done'), listFilters.status === 'done' ? 'ring-1 ring-offset-1 ring-emerald-300' : 'opacity-75 hover:opacity-100']" @click="setStatusFilter('done')">Done {{ statusSummary.done }}</button>
        <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[statusTone('invalid'), listFilters.status === 'invalid' ? 'ring-1 ring-offset-1 ring-rose-300' : 'opacity-75 hover:opacity-100']" @click="setStatusFilter('invalid')">Invalid {{ statusSummary.invalid }}</button>
      </div>
      <div class="mt-2 flex flex-wrap items-center gap-2">
        <span class="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">Priority totals</span>
        <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[priorityTone('low'), listFilters.priority === 'low' ? 'ring-1 ring-offset-1 ring-emerald-300' : 'opacity-75 hover:opacity-100']" @click="setPriorityFilter('low')">Low {{ prioritySummary.low }}</button>
        <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[priorityTone('medium'), listFilters.priority === 'medium' ? 'ring-1 ring-offset-1 ring-amber-300' : 'opacity-75 hover:opacity-100']" @click="setPriorityFilter('medium')">Medium {{ prioritySummary.medium }}</button>
        <button type="button" class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="[priorityTone('high'), listFilters.priority === 'high' ? 'ring-1 ring-offset-1 ring-rose-300' : 'opacity-75 hover:opacity-100']" @click="setPriorityFilter('high')">High {{ prioritySummary.high }}</button>
      </div>
    </article>

    <div v-if="loading" class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 text-sm text-[var(--color-text-muted)]">Loading tickets...</div>
    <div v-else-if="error" class="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{{ error }}</div>
    <div v-else-if="!tickets.length" class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-5 text-sm text-[var(--color-text-secondary)]">No tickets match your filters.</div>

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
              <span>Technician: {{ ticket.assigned_to?.name || 'Unassigned' }}</span>
              <span>Updated: {{ new Date(ticket.updated_at || ticket.created_at).toLocaleDateString() }}</span>
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
