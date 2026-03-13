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

async function loadTickets() {
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
    })
    await loadTickets()
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
  await Promise.all([loadTickets(), loadServices()])
})
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-base font-semibold text-[var(--color-text-primary)]">My tickets</h2>
        <p class="text-sm text-[var(--color-text-secondary)]">Create and manage your maintenance requests.</p>
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
      <div class="grid gap-3 sm:grid-cols-4">
        <input
          v-model="listFilters.q"
          type="text"
          placeholder="Search title/description"
          class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm sm:col-span-2"
          @keyup.enter="applyFilters"
        />
        <select v-model="listFilters.status" class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm">
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="assigned">Assigned</option>
          <option value="in_progress">In progress</option>
          <option value="done">Done</option>
          <option value="invalid">Invalid</option>
        </select>
        <select v-model="listFilters.priority" class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm">
          <option value="">All priorities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </div>
      <div class="mt-3 flex justify-end">
        <button type="button" class="rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white" @click="applyFilters">Apply filters</button>
      </div>
    </article>

    <div v-if="loading" class="text-sm text-[var(--color-text-muted)]">Loading tickets...</div>
    <div v-else-if="error" class="text-sm text-danger-500">{{ error }}</div>
    <div v-else-if="!tickets.length" class="text-sm text-[var(--color-text-secondary)]">No tickets found.</div>

    <div v-else class="space-y-3">
      <article v-for="ticket in tickets" :key="ticket.id" class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
        <p class="text-xs text-[var(--color-text-secondary)]">{{ ticket.status.replace('_', ' ') }}</p>
        <h3 class="mt-1 text-base font-semibold text-[var(--color-text-primary)]">{{ ticket.title }}</h3>
        <p class="mt-1 line-clamp-2 text-sm text-[var(--color-text-secondary)]">{{ ticket.description }}</p>
        <div class="mt-3 flex justify-end">
          <RouterLink :to="`/tickets/${ticket.id}`" class="rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-700">Open</RouterLink>
        </div>
      </article>

      <div class="flex items-center justify-between rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] px-3 py-2 text-xs text-[var(--color-text-secondary)]">
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
