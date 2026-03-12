<script setup>
import { computed, onMounted, ref } from 'vue'
import TicketDetailOverlay from '@/components/dashboard/TicketDetailOverlay.vue'
import { useAuthStore } from '@/stores/auth'
import {
  addTenantTicketComment,
  createTicket,
  deleteTicket,
  deleteTicketImage,
  fetchTenantTickets,
  fetchTicketDetail,
  updateTicket,
  uploadTicketImage,
} from '@/services/dashboard'

const auth = useAuthStore()
const hasManager = computed(() => !!auth.user?.manager_id)

const tickets = ref([])
const loading = ref(true)
const error = ref('')
const statusFilter = ref('')

const showCreateForm = ref(false)
const newTitle = ref('')
const newDescription = ref('')
const newPriority = ref('medium')
const selectedImages = ref([])
const creating = ref(false)
const createError = ref('')

const detailOpen = ref(false)
const detailLoading = ref(false)
const detailTicket = ref(null)
const detailError = ref('')
const editDesc = ref('')
const editPriority = ref('medium')
const saving = ref(false)
const addingImage = ref(false)
const commentSubmitting = ref(false)
const actionSubmitting = ref(false)

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

function validateImageFile(file) {
  if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) {
    return 'Only PNG, JPEG, and WebP images are allowed.'
  }
  if (file.size > 10 * 1024 * 1024) {
    return 'Each image must be smaller than 10MB.'
  }
  return ''
}

function createImageSelection(file) {
  return {
    id: `${file.name}-${file.size}-${file.lastModified}-${Math.random().toString(36).slice(2)}`,
    file,
    name: file.name,
    preview: URL.createObjectURL(file),
  }
}

function revokeSelectedImages() {
  selectedImages.value.forEach((image) => URL.revokeObjectURL(image.preview))
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

async function openTicket(ticketId) {
  detailOpen.value = true
  detailLoading.value = true
  detailError.value = ''
  detailTicket.value = null
  try {
    const { data } = await fetchTicketDetail(ticketId)
    detailTicket.value = data.ticket
    editDesc.value = data.ticket.description
    editPriority.value = data.ticket.priority
  } catch (err) {
    detailError.value = err.response?.data?.message || 'Failed to load ticket details.'
  } finally {
    detailLoading.value = false
  }
}

function closeTicket() {
  detailOpen.value = false
  detailTicket.value = null
  detailError.value = ''
}

async function handleSave() {
  if (!detailTicket.value) return
  saving.value = true
  detailError.value = ''
  try {
    const { data } = await updateTicket(detailTicket.value.id, {
      description: editDesc.value,
      priority: editPriority.value,
    })
    detailTicket.value = data.ticket
    const index = tickets.value.findIndex((ticket) => ticket.id === data.ticket.id)
    if (index !== -1) {
      tickets.value[index] = data.ticket
    }
  } catch (err) {
    detailError.value = err.response?.data?.message || 'Failed to save changes.'
  } finally {
    saving.value = false
  }
}

async function handleAddImage(event) {
  const files = Array.from(event.target.files || [])
  if (!files.length || !detailTicket.value) return

  addingImage.value = true
  detailError.value = ''
  try {
    const uploadedImages = []
    for (const file of files) {
      const validationError = validateImageFile(file)
      if (validationError) {
        throw new Error(validationError)
      }
      const { data } = await uploadTicketImage(detailTicket.value.id, file)
      uploadedImages.push(data.image)
    }
    detailTicket.value.images.push(...uploadedImages)
  } catch (err) {
    detailError.value = err.response?.data?.message || err.message || 'Image upload failed.'
  } finally {
    addingImage.value = false
    event.target.value = ''
  }
}

async function handleDeleteImage(imageId) {
  if (!detailTicket.value) return
  detailError.value = ''
  try {
    await deleteTicketImage(detailTicket.value.id, imageId)
    detailTicket.value.images = detailTicket.value.images.filter((image) => image.id !== imageId)
  } catch (err) {
    detailError.value = err.response?.data?.message || 'Failed to delete image.'
  }
}

async function handleComment(body) {
  if (!detailTicket.value) return
  commentSubmitting.value = true
  detailError.value = ''
  try {
    const { data } = await addTenantTicketComment(detailTicket.value.id, body)
    detailTicket.value = data.ticket
    editDesc.value = data.ticket.description
    editPriority.value = data.ticket.priority
  } catch (err) {
    detailError.value = err.response?.data?.message || 'Failed to send reply.'
  } finally {
    commentSubmitting.value = false
  }
}

async function handleDeleteTicket() {
  if (!detailTicket.value || !window.confirm('Delete this ticket permanently?')) return
  actionSubmitting.value = true
  detailError.value = ''
  try {
    const ticketId = detailTicket.value.id
    await deleteTicket(ticketId)
    tickets.value = tickets.value.filter((ticket) => ticket.id !== ticketId)
    closeTicket()
  } catch (err) {
    detailError.value = err.response?.data?.message || 'Failed to delete ticket.'
  } finally {
    actionSubmitting.value = false
  }
}

function handleImageSelect(event) {
  const files = Array.from(event.target.files || [])
  if (!files.length) return

  const nextImages = []
  for (const file of files) {
    const validationError = validateImageFile(file)
    if (validationError) {
      createError.value = validationError
      event.target.value = ''
      return
    }
    nextImages.push(createImageSelection(file))
  }

  selectedImages.value.push(...nextImages)
  createError.value = ''
  event.target.value = ''
}

function removeSelectedImage(imageId) {
  const image = selectedImages.value.find((item) => item.id === imageId)
  if (image) {
    URL.revokeObjectURL(image.preview)
  }
  selectedImages.value = selectedImages.value.filter((item) => item.id !== imageId)
}

function clearImages() {
  revokeSelectedImages()
  selectedImages.value = []
  const input = document.querySelector('input[data-create-img]')
  if (input) input.value = ''
}

async function handleCreate() {
  createError.value = ''
  creating.value = true
  try {
    const ticketRes = await createTicket({
      title: newTitle.value,
      description: newDescription.value,
      priority: newPriority.value,
    })
    const ticketId = ticketRes.data.ticket.id

    for (const image of selectedImages.value) {
      await uploadTicketImage(ticketId, image.file)
    }

    newTitle.value = ''
    newDescription.value = ''
    newPriority.value = 'medium'
    clearImages()
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
  <div class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 shadow-sm sm:p-6">
    <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
      <h3 class="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">My Tickets</h3>
      <div class="flex w-full items-center gap-2 sm:w-auto">
        <select
          v-model="statusFilter"
          @change="loadTickets"
          class="h-11 flex-1 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 py-2 text-sm text-[var(--color-text-primary)] focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none sm:h-auto sm:flex-initial sm:px-2 sm:py-1 sm:text-xs"
        >
          <option v-for="s in statuses" :key="s" :value="s">{{ statusLabels[s] }}</option>
        </select>
        <button
          v-if="hasManager"
          @click="showCreateForm = !showCreateForm"
          class="h-11 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700 sm:h-auto sm:px-3 sm:py-1.5 sm:text-xs"
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
    <div v-if="showCreateForm" class="mb-4 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] p-3 sm:p-4">
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
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
          <label class="flex min-h-11 w-full cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 py-2 text-sm transition-colors hover:bg-[var(--color-bg-elevated)] sm:w-auto sm:justify-start">
            <span class="text-[var(--color-text-muted)]">📎 Attach images</span>
            <input data-create-img type="file" multiple accept="image/png,image/jpeg,image/webp" @change="handleImageSelect" class="hidden" />
          </label>
          <button v-if="selectedImages.length" @click="clearImages" type="button" class="min-h-11 rounded-lg px-3 py-2 text-sm text-danger-600 transition-colors hover:bg-danger-50">Clear all</button>
        </div>
        <div v-if="selectedImages.length" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="image in selectedImages"
            :key="image.id"
            class="overflow-hidden rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-input)]"
          >
            <div class="relative aspect-4/3 bg-slate-200">
              <img :src="image.preview" :alt="image.name" class="h-full w-full object-cover" />
              <button
                type="button"
                @click="removeSelectedImage(image.id)"
                class="absolute right-2 top-2 rounded-full bg-white/90 px-2 py-1 text-xs font-semibold text-danger-600 shadow-sm hover:bg-white"
              >
                Remove
              </button>
            </div>
            <div class="p-3 text-xs text-[var(--color-text-secondary)]">
              <p class="truncate font-medium text-[var(--color-text-primary)]">{{ image.name }}</p>
            </div>
          </div>
        </div>
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
          <select
            v-model="newPriority"
            class="h-11 w-full rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 py-2 text-sm text-[var(--color-text-primary)] focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none sm:h-auto sm:w-auto sm:px-2"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
          <button
            @click="handleCreate"
            :disabled="creating || newTitle.length < 5 || newDescription.length < 10"
            class="h-11 w-full rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700 disabled:opacity-50 sm:h-auto sm:w-auto"
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

    <div v-else class="space-y-3">
      <article
        v-for="ticket in tickets"
        :key="ticket.id"
        class="flex flex-col gap-3 rounded-[22px] border border-[var(--color-border-default)] bg-[linear-gradient(135deg,var(--color-bg-elevated),#ffffff)] p-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4 sm:p-4"
      >
        <div class="min-w-0">
          <p class="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--color-text-muted)]">{{ new Date(ticket.created_at).toLocaleDateString() }}</p>
          <h4 class="mt-2 truncate text-base font-semibold text-[var(--color-text-primary)]">{{ ticket.title }}</h4>
        </div>
        <div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
          <span :class="statusColors[ticket.status]" class="rounded-full px-3 py-1 text-xs font-semibold capitalize">
            {{ ticket.status.replace('_', ' ') }}
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
      viewer-role="tenant"
      :can-edit-ticket="true"
      :edit-description="editDesc"
      :edit-priority="editPriority"
      :saving="saving"
      :adding-image="addingImage"
      :comment-submitting="commentSubmitting"
      :action-submitting="actionSubmitting"
      :save-error="detailError"
      @close="closeTicket"
      @save="handleSave"
      @add-image="handleAddImage"
      @delete-image="handleDeleteImage"
      @submit-comment="handleComment"
      @delete-ticket="handleDeleteTicket"
      @update:edit-description="editDesc = $event"
      @update:edit-priority="editPriority = $event"
    />
  </div>
</template>
