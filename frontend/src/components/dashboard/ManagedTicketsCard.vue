<script setup>
import { onMounted, ref } from 'vue'
import TicketDetailOverlay from '@/components/dashboard/TicketDetailOverlay.vue'
import TechnicianSearchModal from '@/components/dashboard/TechnicianSearchModal.vue'
import {
  addManagedTicketComment,
  assignTechnicianToTicket,
  fetchManagedTicketDetail,
  fetchManagedTickets,
  markManagedTicketInvalid,
} from '@/services/dashboard'

const tickets = ref([])
const loading = ref(true)
const error = ref('')
const statusFilter = ref('')

const detailOpen = ref(false)
const detailLoading = ref(false)
const detailError = ref('')
const detailTicket = ref(null)
const commentSubmitting = ref(false)
const actionSubmitting = ref(false)
const searchModalOpen = ref(false)

const statuses = ['', 'open', 'assigned', 'in_progress', 'done', 'invalid']
const statusLabels = {
  '': 'All',
  open: 'Open',
  assigned: 'Assigned',
  in_progress: 'In Progress',
  done: 'Done',
  invalid: 'Invalid',
}
const statusColors = {
  open: 'bg-sky-100 text-sky-800',
  assigned: 'bg-amber-100 text-amber-800',
  in_progress: 'bg-blue-100 text-blue-800',
  done: 'bg-emerald-100 text-emerald-800',
  invalid: 'bg-rose-100 text-rose-800',
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

async function openTicket(ticketId) {
  detailOpen.value = true
  detailLoading.value = true
  detailError.value = ''
  detailTicket.value = null
  try {
    const { data } = await fetchManagedTicketDetail(ticketId)
    detailTicket.value = data.ticket
  } catch (err) {
    detailError.value = err.response?.data?.message || 'Failed to load ticket details.'
  } finally {
    detailLoading.value = false
  }
}

function closeTicket() {
  detailOpen.value = false
  detailError.value = ''
  detailTicket.value = null
}

async function handleComment(body) {
  if (!detailTicket.value) return
  commentSubmitting.value = true
  detailError.value = ''
  try {
    const { data } = await addManagedTicketComment(detailTicket.value.id, body)
    detailTicket.value = data.ticket
  } catch (err) {
    detailError.value = err.response?.data?.message || 'Failed to add comment.'
  } finally {
    commentSubmitting.value = false
  }
}

async function handleMarkInvalid() {
  if (!detailTicket.value || detailTicket.value.status === 'invalid') return
  actionSubmitting.value = true
  detailError.value = ''
  try {
    const { data } = await markManagedTicketInvalid(detailTicket.value.id)
    detailTicket.value = data.ticket
    const index = tickets.value.findIndex((ticket) => ticket.id === data.ticket.id)
    if (index !== -1) {
      tickets.value[index] = data.ticket
    }
  } catch (err) {
    detailError.value = err.response?.data?.message || 'Failed to mark ticket invalid.'
  } finally {
    actionSubmitting.value = false
  }
}

function handleFindTechnician() {
  searchModalOpen.value = true
}

function ticketStatusLabel(ticket) {
  if (ticket.technician_request_pending) return 'request pending'
  return ticket.status.replace('_', ' ')
}

async function handleTechnicianSelect(technician) {
  if (!detailTicket.value) return
  actionSubmitting.value = true
  detailError.value = ''
  try {
    const { data } = await assignTechnicianToTicket(detailTicket.value.id, technician.id)
    detailTicket.value = data.ticket

    // Update ticket in list
    const index = tickets.value.findIndex((ticket) => ticket.id === data.ticket.id)
    if (index !== -1) {
      tickets.value[index] = data.ticket
    }
  } catch (err) {
    detailError.value = err.response?.data?.message || 'Failed to send technician request.'
  } finally {
    actionSubmitting.value = false
  }
}

onMounted(loadTickets)
</script>

<template>
  <div class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 shadow-sm sm:p-6">
    <div class="mb-5 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
      <div>
        <h3 class="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Tenant Tickets</h3>
        <p class="mt-1 text-sm text-[var(--color-text-secondary)]">A lightweight queue. Open any ticket to review the full thread and history.</p>
      </div>
      <select
        v-model="statusFilter"
        @change="loadTickets"
        class="h-11 w-full rounded-full border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 py-2 text-sm text-[var(--color-text-primary)] focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none sm:h-auto sm:w-auto sm:text-xs"
      >
        <option v-for="s in statuses" :key="s" :value="s">{{ statusLabels[s] }}</option>
      </select>
    </div>

    <div v-if="loading" class="text-sm text-[var(--color-text-muted)]">Loading...</div>
    <div v-else-if="error" class="text-sm text-danger-500">{{ error }}</div>
    <div v-else-if="tickets.length === 0" class="text-sm text-[var(--color-text-secondary)]">No tickets found.</div>

    <div v-else class="space-y-3">
      <article
        v-for="ticket in tickets"
        :key="ticket.id"
        class="flex flex-col gap-3 rounded-[22px] border border-[var(--color-border-default)] bg-[linear-gradient(135deg,var(--color-bg-elevated),#ffffff)] p-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4 sm:p-4"
      >
        <div class="min-w-0">
          <p class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--color-text-muted)]">{{ ticket.created_by.name }}</p>
          <h4 class="mt-2 truncate text-base font-semibold text-[var(--color-text-primary)]">{{ ticket.title }}</h4>
        </div>

        <div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
          <span :class="statusColors[ticket.status]" class="rounded-full px-3 py-1 text-xs font-semibold capitalize">
            {{ ticketStatusLabel(ticket) }}
          </span>
          <button
            class="min-h-11 w-full rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 sm:min-h-0 sm:w-auto"
            @click="openTicket(ticket.id)"
          >
            Open ticket
          </button>
        </div>
      </article>
    </div>

    <TicketDetailOverlay
      :open="detailOpen"
      :loading="detailLoading"
      :ticket="detailTicket"
      :error="detailError"
      viewer-role="manager"
      :comment-submitting="commentSubmitting"
      :action-submitting="actionSubmitting"
      :save-error="detailError"
      @close="closeTicket"
      @submit-comment="handleComment"
      @mark-invalid="handleMarkInvalid"
      @find-technician="handleFindTechnician"
    />

    <TechnicianSearchModal
      :open="searchModalOpen"
      :ticket-id="detailTicket?.id || ''"
      :default-service-id="detailTicket?.service_tag?.id || ''"
      @close="searchModalOpen = false"
      @select-technician="handleTechnicianSelect"
    />
  </div>
</template>
