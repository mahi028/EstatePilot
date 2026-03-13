<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import TechnicianSearchModal from '@/components/dashboard/TechnicianSearchModal.vue'
import {
  addManagedTicketComment,
  assignTechnicianToTicket,
  fetchManagedTicketDetail,
  markManagedTicketInvalid,
} from '@/services/dashboard'
import { getUploadUrl } from '@/services/dashboard'
import TicketActivityTimeline from '@/components/tickets/TicketActivityTimeline.vue'

const route = useRoute()
const ticketId = ref(String(route.params.ticketId || ''))

const ticket = ref(null)
const loading = ref(true)
const error = ref('')
const commentText = ref('')
const commentSubmitting = ref(false)
const actionSubmitting = ref(false)
const searchModalOpen = ref(false)

async function loadTicket() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await fetchManagedTicketDetail(ticketId.value)
    ticket.value = data.ticket
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to load ticket.'
  } finally {
    loading.value = false
  }
}

async function submitComment() {
  const body = commentText.value.trim()
  if (!body) return
  commentSubmitting.value = true
  error.value = ''
  try {
    const { data } = await addManagedTicketComment(ticketId.value, body)
    ticket.value = data.ticket
    commentText.value = ''
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to post comment.'
  } finally {
    commentSubmitting.value = false
  }
}

async function markInvalid() {
  if (!ticket.value || ticket.value.status === 'invalid') return
  if (!window.confirm('Mark this ticket as invalid?')) return
  actionSubmitting.value = true
  error.value = ''
  try {
    const { data } = await markManagedTicketInvalid(ticketId.value)
    ticket.value = data.ticket
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to mark invalid.'
  } finally {
    actionSubmitting.value = false
  }
}

function openAssignTechnician() {
  searchModalOpen.value = true
}

async function assignTechnician(technician) {
  if (!ticket.value) return
  actionSubmitting.value = true
  error.value = ''
  try {
    const { data } = await assignTechnicianToTicket(ticket.value.id, technician.id)
    ticket.value = data.ticket
    searchModalOpen.value = false
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to assign technician.'
  } finally {
    actionSubmitting.value = false
  }
}

onMounted(loadTicket)
watch(() => route.params.ticketId, (value) => {
  ticketId.value = String(value || '')
  searchModalOpen.value = false
  loadTicket()
})
</script>

<template>
  <div>
    <div v-if="loading" class="text-sm text-[var(--color-text-muted)]">Loading ticket...</div>
    <div v-else-if="error" class="text-sm text-danger-500">{{ error }}</div>
    <div v-else-if="ticket" class="space-y-4">
      <article class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-xs text-[var(--color-text-secondary)]">{{ ticket.created_by.name }}</p>
            <h2 class="text-xl font-semibold text-[var(--color-text-primary)]">{{ ticket.title }}</h2>
          </div>
          <div class="flex flex-wrap justify-end gap-2">
            <button
              type="button"
              class="rounded-lg bg-primary-600 px-3 py-2 text-xs font-semibold text-white hover:bg-primary-700 disabled:opacity-60"
              :disabled="actionSubmitting || ticket.status === 'invalid'"
              @click="openAssignTechnician"
            >
              {{ ticket.assigned_to ? 'Change technician' : 'Assign technician' }}
            </button>
            <button class="rounded-lg bg-rose-600 px-3 py-2 text-xs font-semibold text-white disabled:opacity-60" :disabled="actionSubmitting || ticket.status === 'invalid'" @click="markInvalid">
              {{ actionSubmitting ? 'Updating...' : 'Mark invalid' }}
            </button>
          </div>
        </div>
        <p class="mt-2 whitespace-pre-line text-sm text-[var(--color-text-secondary)]">{{ ticket.description }}</p>
      </article>

      <article class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
        <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Assignment</p>
        <div class="mt-3 grid gap-2 text-sm text-[var(--color-text-secondary)]">
          <p><span class="font-medium text-[var(--color-text-primary)]">Technician:</span> {{ ticket.assigned_to?.name || 'Not assigned' }}</p>
          <p><span class="font-medium text-[var(--color-text-primary)]">Status:</span> {{ ticket.technician_request_pending ? 'Request pending' : 'No pending request' }}</p>
        </div>
      </article>

      <article class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
        <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Attachments</p>
        <div v-if="ticket.images?.length" class="mt-3 grid gap-3 sm:grid-cols-2">
          <img v-for="img in ticket.images" :key="img.id" :src="getUploadUrl(img.file_path)" alt="ticket" class="h-40 w-full rounded-xl object-cover" />
        </div>
        <p v-else class="mt-3 text-sm text-[var(--color-text-secondary)]">No attachments.</p>
      </article>

      <article class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
        <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Conversation</p>
        <div class="mt-3 space-y-2">
          <div v-for="comment in ticket.comments || []" :key="comment.id" class="rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] p-3">
            <p class="text-xs font-semibold text-[var(--color-text-primary)]">{{ comment.user.name }} ({{ comment.user.role }})</p>
            <p class="mt-1 text-sm text-[var(--color-text-secondary)]">{{ comment.body }}</p>
          </div>
          <p v-if="!(ticket.comments || []).length" class="text-sm text-[var(--color-text-secondary)]">No comments yet.</p>
        </div>

        <div class="mt-3">
          <textarea v-model="commentText" rows="3" class="w-full rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] p-3 text-sm" placeholder="Add comment..."></textarea>
          <button class="mt-2 rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white disabled:opacity-60" :disabled="commentSubmitting || !commentText.trim()" @click="submitComment">
            {{ commentSubmitting ? 'Sending...' : 'Send reply' }}
          </button>
        </div>
      </article>

      <TicketActivityTimeline :logs="ticket.activity_logs || []" />
    </div>

    <TechnicianSearchModal
      :open="searchModalOpen"
      :ticket-id="ticket?.id || ''"
      :default-service-id="ticket?.service_tag?.id || ''"
      @close="searchModalOpen = false"
      @select-technician="assignTechnician"
    />
  </div>
</template>
