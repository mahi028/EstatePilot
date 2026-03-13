<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { fetchManagedTickets } from '@/services/dashboard'

const tickets = ref([])
const filters = ref({ q: '', status: '', priority: '', page: 1, page_size: 8 })
const pagination = ref({ page: 1, page_size: 8, total: 0, total_pages: 0 })
const loading = ref(true)
const error = ref('')

async function loadTickets() {
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

function goToPage(nextPage) {
  if (nextPage < 1 || nextPage > (pagination.value.total_pages || 1)) return
  filters.value.page = nextPage
  loadTickets()
}

onMounted(loadTickets)
</script>

<template>
  <div class="space-y-3">
    <article class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
      <div class="grid gap-3 sm:grid-cols-4">
        <input
          v-model="filters.q"
          type="text"
          placeholder="Search title/tenant"
          class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm sm:col-span-2"
          @keyup.enter="applyFilters"
        />
        <select v-model="filters.status" class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm">
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="assigned">Assigned</option>
          <option value="in_progress">In progress</option>
          <option value="done">Done</option>
          <option value="invalid">Invalid</option>
        </select>
        <select v-model="filters.priority" class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm">
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
        <p class="text-xs text-[var(--color-text-secondary)]">{{ ticket.created_by.name }} • {{ ticket.status.replace('_', ' ') }}</p>
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
