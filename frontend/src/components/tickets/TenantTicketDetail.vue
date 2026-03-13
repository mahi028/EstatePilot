<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  addTenantTicketComment,
  deleteTicket,
  deleteTicketImage,
  fetchTicketDetail,
  updateTicket,
  uploadTicketImage,
} from '@/services/dashboard'
import { getUploadUrl } from '@/services/dashboard'
import TicketActivityTimeline from '@/components/tickets/TicketActivityTimeline.vue'

const route = useRoute()
const router = useRouter()
const ticketId = ref(String(route.params.ticketId || ''))

const ticket = ref(null)
const loading = ref(true)
const error = ref('')
const commentText = ref('')
const submitting = ref(false)
const isEditing = ref(false)
const editDescription = ref('')
const editPriority = ref('medium')
const saving = ref(false)
const addingImage = ref(false)
const actionSubmitting = ref(false)

async function loadTicket() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await fetchTicketDetail(ticketId.value)
    ticket.value = data.ticket
    editDescription.value = data.ticket.description || ''
    editPriority.value = data.ticket.priority || 'medium'
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to load ticket.'
  } finally {
    loading.value = false
  }
}

async function submitComment() {
  const body = commentText.value.trim()
  if (!body) return
  submitting.value = true
  error.value = ''
  try {
    const { data } = await addTenantTicketComment(ticketId.value, body)
    ticket.value = data.ticket
    commentText.value = ''
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to post comment.'
  } finally {
    submitting.value = false
  }
}

function startEditing() {
  if (!ticket.value) return
  editDescription.value = ticket.value.description || ''
  editPriority.value = ticket.value.priority || 'medium'
  isEditing.value = true
}

function cancelEditing() {
  isEditing.value = false
  if (!ticket.value) return
  editDescription.value = ticket.value.description || ''
  editPriority.value = ticket.value.priority || 'medium'
}

async function saveTicket() {
  if (!ticket.value) return
  saving.value = true
  error.value = ''
  try {
    const { data } = await updateTicket(ticket.value.id, {
      description: editDescription.value,
      priority: editPriority.value,
    })
    ticket.value = data.ticket
    isEditing.value = false
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to save changes.'
  } finally {
    saving.value = false
  }
}

async function addImages(event) {
  const files = Array.from(event.target.files || [])
  if (!ticket.value || !files.length) return

  addingImage.value = true
  error.value = ''
  try {
    const uploaded = []
    for (const file of files) {
      const { data } = await uploadTicketImage(ticket.value.id, file)
      uploaded.push(data.image)
    }
    ticket.value.images = [...(ticket.value.images || []), ...uploaded]
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to upload image.'
  } finally {
    addingImage.value = false
    event.target.value = ''
  }
}

async function removeImage(imageId) {
  if (!ticket.value) return
  error.value = ''
  try {
    await deleteTicketImage(ticket.value.id, imageId)
    ticket.value.images = (ticket.value.images || []).filter((image) => image.id !== imageId)
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to remove image.'
  }
}

async function removeTicket() {
  if (!ticket.value || !window.confirm('Delete this ticket permanently?')) return
  actionSubmitting.value = true
  error.value = ''
  try {
    await deleteTicket(ticket.value.id)
    router.push('/tickets')
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to delete ticket.'
  } finally {
    actionSubmitting.value = false
  }
}

onMounted(loadTicket)
watch(() => route.params.ticketId, (value) => {
  ticketId.value = String(value || '')
  isEditing.value = false
  loadTicket()
})
</script>

<template>
  <div>
    <div v-if="loading" class="text-sm text-[var(--color-text-muted)]">Loading ticket...</div>
    <div v-else-if="error" class="text-sm text-danger-500">{{ error }}</div>
    <div v-else-if="ticket" class="space-y-4">
      <article class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 class="text-xl font-semibold text-[var(--color-text-primary)]">{{ ticket.title }}</h2>
            <p class="mt-1 text-sm text-[var(--color-text-secondary)]">Status: {{ ticket.status.replace('_', ' ') }}</p>
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              v-if="!isEditing"
              type="button"
              class="rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] px-3 py-2 text-sm font-medium"
              @click="startEditing"
            >
              Edit ticket
            </button>
            <button
              type="button"
              class="rounded-lg bg-rose-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
              :disabled="actionSubmitting"
              @click="removeTicket"
            >
              {{ actionSubmitting ? 'Deleting...' : 'Delete ticket' }}
            </button>
          </div>
        </div>

        <div v-if="isEditing" class="mt-4 space-y-3">
          <textarea
            v-model="editDescription"
            rows="5"
            class="w-full rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] p-3 text-sm"
          ></textarea>
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <select v-model="editPriority" class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
            <div class="flex gap-2">
              <button type="button" class="rounded-lg border border-[var(--color-border-default)] px-3 py-2 text-sm" @click="cancelEditing">Cancel</button>
              <button type="button" class="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-60" :disabled="saving || editDescription.trim().length < 10" @click="saveTicket">
                {{ saving ? 'Saving...' : 'Save changes' }}
              </button>
            </div>
          </div>
        </div>

        <p v-else class="mt-2 whitespace-pre-line text-sm text-[var(--color-text-secondary)]">{{ ticket.description }}</p>
      </article>

      <article class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Attachments</p>
          <label class="inline-flex cursor-pointer items-center rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] px-3 py-2 text-sm">
            {{ addingImage ? 'Uploading...' : 'Add images' }}
            <input type="file" accept="image/png,image/jpeg,image/webp" multiple class="hidden" :disabled="addingImage" @change="addImages" />
          </label>
        </div>
        <div v-if="ticket.images?.length" class="mt-3 grid gap-3 sm:grid-cols-2">
          <div v-for="img in ticket.images" :key="img.id" class="overflow-hidden rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)]">
            <img :src="getUploadUrl(img.file_path)" alt="ticket" class="h-40 w-full object-cover" />
            <div class="flex items-center justify-between gap-3 p-3">
              <p class="truncate text-xs text-[var(--color-text-secondary)]">{{ img.file_path.split('/').pop() }}</p>
              <button type="button" class="text-xs font-medium text-rose-700" @click="removeImage(img.id)">Remove</button>
            </div>
          </div>
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
          <button class="mt-2 rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white disabled:opacity-60" :disabled="submitting || !commentText.trim()" @click="submitComment">
            {{ submitting ? 'Sending...' : 'Send reply' }}
          </button>
        </div>
      </article>

      <TicketActivityTimeline :logs="ticket.activity_logs || []" />
    </div>
  </div>
</template>
