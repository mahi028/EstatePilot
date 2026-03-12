<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { fetchTenantTickets, createTicket } from '@/services/dashboard'

const auth = useAuthStore()
const hasManager = computed(() => !!auth.user?.manager_id)

const tickets = ref([])
const loading = ref(true)
const error = ref('')
const statusFilter = ref('')

// Create ticket state
const showCreateForm = ref(false)
const newTitle = ref('')
const newDescription = ref('')
const newPriority = ref('medium')
const creating = ref(false)
const createError = ref('')

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
    const { data } = await fetchTenantTickets(params)
    tickets.value = data.tickets
  } catch {
    error.value = 'Failed to load tickets.'
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  createError.value = ''
  creating.value = true
  try {
    await createTicket({
      title: newTitle.value,
      description: newDescription.value,
      priority: newPriority.value,
    })
    newTitle.value = ''
    newDescription.value = ''
    newPriority.value = 'medium'
    showCreateForm.value = false
    await loadTickets()
  } catch (err) {
    createError.value = err.response?.data?.message || err.response?.data?.errors?.title?.[0] || 'Failed to create ticket.'
  } finally {
    creating.value = false
  }
}

onMounted(loadTickets)
</script>

<template>
  <div class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-6 shadow-sm">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
      <h3 class="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">My Tickets</h3>
      <div class="flex items-center gap-2">
        <select
          v-model="statusFilter"
          @change="loadTickets"
          class="rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-2 py-1 text-xs text-[var(--color-text-primary)] focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
        >
          <option v-for="s in statuses" :key="s" :value="s">{{ statusLabels[s] }}</option>
        </select>
        <button
          v-if="hasManager"
          @click="showCreateForm = !showCreateForm"
          class="rounded-lg bg-primary-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-primary-700 transition-colors"
        >
          {{ showCreateForm ? 'Cancel' : '+ New Ticket' }}
        </button>
      </div>
    </div>

    <!-- No manager warning -->
    <div v-if="!hasManager" class="mb-4 rounded-lg bg-accent-50 p-3 text-xs text-accent-700">
      You need a manager assigned before you can create tickets.
    </div>

    <!-- Create ticket form -->
    <div v-if="showCreateForm" class="mb-4 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] p-4">
      <h4 class="mb-3 text-sm font-medium text-[var(--color-text-primary)]">Create New Ticket</h4>
      <div class="space-y-3">
        <input
          v-model="newTitle"
          type="text"
          placeholder="Ticket title (min 5 characters)"
          class="w-full rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
        />
        <textarea
          v-model="newDescription"
          rows="3"
          placeholder="Describe the issue in detail (min 10 characters)"
          class="w-full rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
        ></textarea>
        <div class="flex items-center gap-3">
          <select
            v-model="newPriority"
            class="rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-2 py-2 text-sm text-[var(--color-text-primary)] focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
          <button
            @click="handleCreate"
            :disabled="creating || newTitle.length < 5 || newDescription.length < 10"
            class="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50 transition-colors"
          >
            {{ creating ? 'Creating...' : 'Create Ticket' }}
          </button>
        </div>
        <p v-if="createError" class="text-sm text-danger-500">{{ createError }}</p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-sm text-[var(--color-text-muted)]">Loading...</div>

    <!-- Error -->
    <div v-else-if="error" class="text-sm text-danger-500">{{ error }}</div>

    <!-- Empty -->
    <div v-else-if="tickets.length === 0" class="text-sm text-[var(--color-text-secondary)]">
      No tickets found.
    </div>

    <!-- Tickets list -->
    <div v-else class="space-y-3">
      <div
        v-for="ticket in tickets"
        :key="ticket.id"
        class="rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] p-4"
      >
        <div class="flex items-start justify-between gap-2">
          <h4 class="text-sm font-medium text-[var(--color-text-primary)]">{{ ticket.title }}</h4>
          <div class="flex flex-shrink-0 gap-1.5">
            <span :class="statusColors[ticket.status]" class="inline-block rounded-full px-2 py-0.5 text-xs font-medium capitalize">
              {{ ticket.status.replace('_', ' ') }}
            </span>
            <span :class="priorityColors[ticket.priority]" class="inline-block rounded-full px-2 py-0.5 text-xs font-medium capitalize">
              {{ ticket.priority }}
            </span>
          </div>
        </div>
        <p class="mt-1 text-xs text-[var(--color-text-secondary)] line-clamp-2">{{ ticket.description }}</p>
        <p class="mt-2 text-xs text-[var(--color-text-muted)]">
          {{ new Date(ticket.created_at).toLocaleDateString() }}
        </p>
      </div>
    </div>
  </div>
</template>
