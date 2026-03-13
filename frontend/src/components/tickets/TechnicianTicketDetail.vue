<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  fetchTechnicianServiceAreaTicketDetail,
  fetchTechnicianTicketDetail,
  acceptTechnicianTicket,
  rejectTechnicianTicket,
  updateTechnicianTicketStatus,
  addTechnicianTicketComment,
  submitTechnicianBid,
} from '@/services/dashboard'
import { getUploadUrl } from '@/services/dashboard'
import TicketActivityTimeline from '@/components/tickets/TicketActivityTimeline.vue'

const route = useRoute()
const router = useRouter()

const scope = computed(() => String(route.query.scope || 'assigned'))
const isPreview = computed(() => scope.value === 'service-area')
const ticketId = computed(() => String(route.params.ticketId || ''))

const loading = ref(true)
const error = ref('')
const ticket = ref(null)

const actionSubmitting = ref(false)
const commentSubmitting = ref(false)
const commentText = ref('')

const bidPrice = ref('')
const bidMessage = ref('')
const bidSubmitting = ref(false)
const bidError = ref('')

const canComment = computed(() => {
  if (isPreview.value || !ticket.value) return false
  return !ticket.value.technician_request_pending && ['assigned', 'in_progress', 'done'].includes(ticket.value.status)
})

async function loadTicket() {
  if (!ticketId.value) return
  loading.value = true
  error.value = ''
  ticket.value = null
  try {
    const res = isPreview.value
      ? await fetchTechnicianServiceAreaTicketDetail(ticketId.value)
      : await fetchTechnicianTicketDetail(ticketId.value)
    ticket.value = res.data.ticket
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to load ticket.'
  } finally {
    loading.value = false
  }
}

async function acceptRequest() {
  if (!ticket.value) return
  actionSubmitting.value = true
  error.value = ''
  try {
    const { data } = await acceptTechnicianTicket(ticket.value.id)
    ticket.value = data.ticket
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to accept request.'
  } finally {
    actionSubmitting.value = false
  }
}

async function rejectRequest() {
  if (!ticket.value) return
  if (!window.confirm('Decline this request?')) return
  actionSubmitting.value = true
  error.value = ''
  try {
    await rejectTechnicianTicket(ticket.value.id)
    router.push('/tickets')
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to decline request.'
  } finally {
    actionSubmitting.value = false
  }
}

async function submitComment() {
  const body = commentText.value.trim()
  if (!ticket.value || !canComment.value || !body) return
  commentSubmitting.value = true
  error.value = ''
  try {
    const { data } = await addTechnicianTicketComment(ticket.value.id, body)
    ticket.value = data.ticket
    commentText.value = ''
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to add comment.'
  } finally {
    commentSubmitting.value = false
  }
}

async function submitBid() {
  if (!isPreview.value || !ticket.value) return
  const value = Number(bidPrice.value)
  if (!value || value <= 0) {
    bidError.value = 'Enter a valid positive bid price.'
    return
  }

  bidSubmitting.value = true
  bidError.value = ''
  error.value = ''
  try {
    await submitTechnicianBid(ticket.value.id, {
      proposed_price: value,
      message: bidMessage.value,
    })
    router.push('/tickets')
  } catch (err) {
    bidError.value = err.response?.data?.message || 'Failed to submit bid.'
  } finally {
    bidSubmitting.value = false
  }
}

async function updateStatus(status) {
  if (!ticket.value) return
  actionSubmitting.value = true
  error.value = ''
  try {
    const { data } = await updateTechnicianTicketStatus(ticket.value.id, status)
    ticket.value = data.ticket
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to update status.'
  } finally {
    actionSubmitting.value = false
  }
}

onMounted(loadTicket)
</script>

<template>
  <div>
    <div v-if="loading" class="text-sm text-[var(--color-text-muted)]">Loading ticket...</div>
    <div v-else-if="error" class="text-sm text-danger-500">{{ error }}</div>
    <div v-else-if="ticket" class="space-y-4">
      <article class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
        <h2 class="text-xl font-semibold text-[var(--color-text-primary)]">{{ ticket.title }}</h2>
        <p class="mt-2 whitespace-pre-line text-sm text-[var(--color-text-secondary)]">{{ ticket.description }}</p>
      </article>

      <article class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
        <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Attachments</p>
        <div v-if="ticket.images?.length" class="mt-3 grid gap-3 sm:grid-cols-2">
          <img v-for="img in ticket.images" :key="img.id" :src="getUploadUrl(img.file_path)" alt="ticket" class="h-40 w-full rounded-xl object-cover" />
        </div>
        <p v-else class="mt-3 text-sm text-[var(--color-text-secondary)]">No attachments.</p>
      </article>

      <article v-if="isPreview" class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
        <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Place bid</p>
        <div class="mt-3 space-y-2">
          <input v-model="bidPrice" type="number" min="1" step="0.01" placeholder="Bid price" class="h-11 w-full rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm" />
          <textarea v-model="bidMessage" rows="3" placeholder="Optional message" class="w-full rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] p-3 text-sm"></textarea>
          <p v-if="bidError" class="text-xs text-rose-700">{{ bidError }}</p>
          <button class="rounded-lg bg-primary-600 px-3 py-2 text-xs font-semibold text-white disabled:opacity-60" :disabled="bidSubmitting" @click="submitBid">
            {{ bidSubmitting ? 'Submitting...' : 'Submit bid' }}
          </button>
        </div>
      </article>

      <article v-if="!isPreview" class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
        <div class="flex flex-wrap gap-2">
          <button
            class="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white disabled:opacity-60"
            :disabled="actionSubmitting || !ticket.technician_request_pending"
            @click="acceptRequest"
          >
            {{ actionSubmitting ? 'Updating...' : 'Accept request' }}
          </button>
          <button
            class="rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] px-3 py-2 text-xs font-semibold"
            :disabled="actionSubmitting || !ticket.technician_request_pending"
            @click="rejectRequest"
          >
            Decline request
          </button>
          <button
            v-if="!ticket.technician_request_pending && ticket.status === 'assigned'"
            class="rounded-lg bg-sky-600 px-3 py-2 text-xs font-semibold text-white disabled:opacity-60"
            :disabled="actionSubmitting"
            @click="updateStatus('in_progress')"
          >
            Start work
          </button>
          <button
            v-if="!ticket.technician_request_pending && ticket.status === 'in_progress'"
            class="rounded-lg bg-emerald-700 px-3 py-2 text-xs font-semibold text-white disabled:opacity-60"
            :disabled="actionSubmitting"
            @click="updateStatus('done')"
          >
            Mark done
          </button>
        </div>
      </article>

      <article v-if="!isPreview" class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
        <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Conversation</p>
        <div class="mt-3 space-y-2">
          <div v-for="comment in ticket.comments || []" :key="comment.id" class="rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] p-3">
            <p class="text-xs font-semibold text-[var(--color-text-primary)]">{{ comment.user.name }} ({{ comment.user.role }})</p>
            <p class="mt-1 text-sm text-[var(--color-text-secondary)]">{{ comment.body }}</p>
          </div>
          <p v-if="!(ticket.comments || []).length" class="text-sm text-[var(--color-text-secondary)]">No comments yet.</p>
        </div>

        <div class="mt-3">
          <textarea v-model="commentText" rows="3" class="w-full rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] p-3 text-sm" :placeholder="canComment ? 'Add update...' : 'Accept request first to comment'" :disabled="!canComment"></textarea>
          <button class="mt-2 rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white disabled:opacity-60" :disabled="commentSubmitting || !canComment || !commentText.trim()" @click="submitComment">
            {{ commentSubmitting ? 'Sending...' : 'Send reply' }}
          </button>
        </div>
      </article>

      <TicketActivityTimeline v-if="!isPreview" :logs="ticket.activity_logs || []" />
    </div>
  </div>
</template>
