<script setup>
import { computed, ref, watch } from 'vue'
import { getUploadUrl } from '@/services/dashboard'

const props = defineProps({
  open: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  ticket: { type: Object, default: null },
  error: { type: String, default: '' },
  viewerRole: { type: String, required: true },
  canEditTicket: { type: Boolean, default: false },
  editDescription: { type: String, default: '' },
  editPriority: { type: String, default: 'medium' },
  saving: { type: Boolean, default: false },
  addingImage: { type: Boolean, default: false },
  commentSubmitting: { type: Boolean, default: false },
  actionSubmitting: { type: Boolean, default: false },
  saveError: { type: String, default: '' },
  canComment: { type: Boolean, default: true },
  commentPlaceholder: { type: String, default: '' },
})

const emit = defineEmits([
  'close',
  'update:editDescription',
  'update:editPriority',
  'save',
  'add-image',
  'delete-image',
  'submit-comment',
  'delete-ticket',
  'mark-invalid',
  'find-technician',
  'accept-ticket',
  'reject-ticket',
])

const commentText = ref('')

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    commentText.value = ''
  }
})

watch(() => props.ticket?.id, () => {
  commentText.value = ''
})

const statusColors = {
  open: 'bg-sky-100 text-sky-800',
  assigned: 'bg-amber-100 text-amber-800',
  in_progress: 'bg-blue-100 text-blue-800',
  done: 'bg-emerald-100 text-emerald-800',
  invalid: 'bg-rose-100 text-rose-800',
}

const priorityColors = {
  low: 'bg-stone-200 text-stone-700',
  medium: 'bg-orange-100 text-orange-800',
  high: 'bg-red-100 text-red-800',
}

const formattedStatus = computed(() => {
  const status = props.ticket?.status
  if (!status) return ''
  if (props.viewerRole === 'technician' && status === 'assigned') return 'requested'
  return status.replace('_', ' ')
})

const viewerLabel = computed(() => {
  if (props.viewerRole === 'manager') return 'Manager View'
  if (props.viewerRole === 'technician') return 'Technician View'
  return 'Tenant View'
})

const resolvedCommentPlaceholder = computed(() => {
  if (props.commentPlaceholder) return props.commentPlaceholder
  if (props.viewerRole === 'manager') return 'Add a note for the tenant...'
  if (props.viewerRole === 'technician') return 'Add a ticket update after accepting...'
  return 'Reply on this ticket...'
})

function submitComment() {
  const body = commentText.value.trim()
  if (!body) return
  emit('submit-comment', body)
  commentText.value = ''
}

function imageUrl(filePath) {
  return getUploadUrl(filePath)
}
</script>

<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-end justify-center p-0 sm:items-center sm:p-6">
    <button
      class="absolute inset-0 bg-slate-950/55 backdrop-blur-sm"
      @click="emit('close')"
      aria-label="Close ticket details"
    ></button>

    <div class="relative z-10 flex h-[100dvh] max-h-[100dvh] w-full max-w-6xl flex-col overflow-hidden rounded-none border border-slate-200 bg-[linear-gradient(180deg,#fffdf8_0%,#ffffff_22%,#f7f9fc_100%)] shadow-[0_30px_120px_rgba(15,23,42,0.28)] sm:h-auto sm:max-h-[92vh] sm:rounded-[28px]">
      <div class="sticky top-0 z-20 flex items-start justify-between gap-4 border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur-sm sm:px-8 sm:py-6">
        <div class="min-w-0">
          <p class="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">
            {{ viewerLabel }}
          </p>
          <h3 class="mt-1 truncate font-serif text-xl text-slate-900 sm:mt-2 sm:text-3xl">
            {{ ticket?.title || 'Ticket details' }}
          </h3>
          <div v-if="ticket" class="mt-3 flex flex-wrap items-center gap-2">
            <span :class="statusColors[ticket.status]" class="rounded-full px-3 py-1 text-xs font-semibold capitalize">
              {{ formattedStatus }}
            </span>
            <span :class="priorityColors[ticket.priority]" class="rounded-full px-3 py-1 text-xs font-semibold capitalize">
              {{ ticket.priority }} priority
            </span>
            <span class="text-xs text-slate-500">
              Opened {{ new Date(ticket.created_at).toLocaleString() }}
            </span>
          </div>
        </div>

        <button
          class="min-h-10 rounded-full border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 transition hover:border-slate-300 hover:text-slate-900"
          @click="emit('close')"
        >
          Close
        </button>
      </div>

      <div class="min-h-0 flex-1 overflow-y-auto px-4 py-4 sm:px-8 sm:py-6">
        <div v-if="loading" class="rounded-2xl border border-slate-200 bg-white/80 p-6 text-sm text-slate-500">
          Loading ticket details...
        </div>

        <div v-else-if="error" class="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
          {{ error }}
        </div>

        <div v-else-if="ticket" class="grid gap-6 lg:grid-cols-[1.35fr_0.95fr]">
          <section class="space-y-6">
            <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <article class="rounded-2xl border border-slate-200 bg-white p-4">
                <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Tenant</p>
                <p class="mt-2 text-sm font-semibold text-slate-900">{{ ticket.created_by.name }}</p>
                <p class="mt-1 text-xs text-slate-500">{{ ticket.created_by.email }}</p>
              </article>

              <article class="rounded-2xl border border-slate-200 bg-white p-4">
                <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Technician</p>
                <p class="mt-2 text-sm font-semibold text-slate-900">{{ ticket.assigned_to?.name || 'Unassigned' }}</p>
                <p class="mt-1 text-xs text-slate-500">{{ ticket.assigned_to?.email || 'No technician yet' }}</p>
              </article>

              <article class="rounded-2xl border border-slate-200 bg-white p-4">
                <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Updated</p>
                <p class="mt-2 text-sm font-semibold text-slate-900">{{ new Date(ticket.updated_at || ticket.created_at).toLocaleDateString() }}</p>
                <p class="mt-1 text-xs text-slate-500">Latest change recorded</p>
              </article>

              <article class="rounded-2xl border border-slate-200 bg-white p-4">
                <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Conversation</p>
                <p class="mt-2 text-sm font-semibold text-slate-900">{{ ticket.comments?.length || 0 }} comments</p>
                <p class="mt-1 text-xs text-slate-500">Thread stays with the ticket</p>
              </article>
            </div>

            <article class="rounded-3xl border border-slate-200 bg-white p-4 sm:p-5">
              <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Description</p>
                  <p class="mt-1 text-xs text-slate-500">Full issue context and any tenant updates.</p>
                </div>
                <button
                  v-if="canEditTicket"
                  class="min-h-11 w-full rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:opacity-60 sm:min-h-0 sm:w-auto sm:text-xs"
                  :disabled="saving || editDescription.trim().length < 10"
                  @click="emit('save')"
                >
                  {{ saving ? 'Saving...' : 'Save changes' }}
                </button>
              </div>

              <textarea
                v-if="canEditTicket"
                :value="editDescription"
                rows="6"
                class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                @input="emit('update:editDescription', $event.target.value)"
              ></textarea>

              <p v-else class="whitespace-pre-line rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm leading-6 text-slate-700">
                {{ ticket.description }}
              </p>

              <div v-if="canEditTicket" class="mt-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
                <select
                  :value="editPriority"
                  class="min-h-11 w-full rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-900 outline-none transition focus:border-slate-400 sm:min-h-0 sm:w-auto"
                  @change="emit('update:editPriority', $event.target.value)"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>

                <label class="inline-flex min-h-11 w-full cursor-pointer items-center justify-center gap-2 rounded-full border border-dashed border-slate-300 bg-slate-50 px-4 py-2 text-sm text-slate-600 transition hover:border-slate-400 hover:bg-white sm:min-h-0 sm:w-auto sm:justify-start">
                  {{ addingImage ? 'Uploading...' : 'Add images' }}
                  <input
                    class="hidden"
                    type="file"
                    multiple
                    accept="image/png,image/jpeg,image/webp"
                    :disabled="addingImage"
                    @change="emit('add-image', $event)"
                  />
                </label>
              </div>
            </article>

            <article class="rounded-3xl border border-slate-200 bg-white p-4 sm:p-5">
              <div class="mb-3 flex items-center justify-between gap-3">
                <div>
                  <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Attachments</p>
                  <p class="mt-1 text-xs text-slate-500">Stored image records for this ticket.</p>
                </div>
              </div>

              <div v-if="ticket.images?.length" class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                <div
                  v-for="image in ticket.images"
                  :key="image.id"
                  class="overflow-hidden rounded-2xl border border-slate-200 bg-slate-50"
                >
                  <div class="relative aspect-4/3 bg-slate-200">
                    <img
                      :src="imageUrl(image.file_path)"
                      :alt="image.file_path.split('/').pop()"
                      class="h-full w-full object-cover"
                    />
                    <button
                      v-if="canEditTicket"
                      class="absolute right-3 top-3 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-rose-700 shadow-sm transition hover:bg-white"
                      @click="emit('delete-image', image.id)"
                    >
                      Remove
                    </button>
                  </div>
                  <div class="p-3">
                    <p class="truncate text-sm font-medium text-slate-900">{{ image.file_path.split('/').pop() }}</p>
                    <p class="mt-1 text-xs text-slate-500">{{ new Date(image.uploaded_at).toLocaleString() }}</p>
                  </div>
                </div>
              </div>
              <p v-else class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-5 text-sm text-slate-500">
                No images attached.
              </p>
            </article>

            <article class="rounded-3xl border border-slate-200 bg-white p-4 sm:p-5">
              <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Activity</p>
              <div v-if="ticket.activity_logs?.length" class="mt-4 space-y-3">
                <div
                  v-for="log in ticket.activity_logs"
                  :key="log.id"
                  class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3"
                >
                  <p class="text-sm text-slate-800">{{ log.action }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ new Date(log.created_at).toLocaleString() }}</p>
                </div>
              </div>
              <p v-else class="mt-4 text-sm text-slate-500">No activity recorded yet.</p>
            </article>
          </section>

          <section class="space-y-6">
            <article class="rounded-3xl border border-slate-200 bg-white p-4 sm:p-5">
              <div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
                <button
                  v-if="viewerRole === 'manager'"
                  class="min-h-11 w-full rounded-full border border-slate-300 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-white sm:min-h-0 sm:w-auto"
                  @click="emit('find-technician')"
                >
                  Request technician
                </button>

                <button
                  v-if="viewerRole === 'manager'"
                  class="min-h-11 w-full rounded-full bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-700 disabled:opacity-60 sm:min-h-0 sm:w-auto"
                  :disabled="actionSubmitting || ticket.status === 'invalid'"
                  @click="emit('mark-invalid')"
                >
                  {{ actionSubmitting ? 'Updating...' : 'Mark as invalid' }}
                </button>

                <button
                  v-if="viewerRole === 'tenant'"
                  class="min-h-11 w-full rounded-full bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-700 disabled:opacity-60 sm:min-h-0 sm:w-auto"
                  :disabled="actionSubmitting"
                  @click="emit('delete-ticket')"
                >
                  {{ actionSubmitting ? 'Deleting...' : 'Delete ticket' }}
                </button>

                <button
                  v-if="viewerRole === 'technician'"
                  class="min-h-11 w-full rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-60 sm:min-h-0 sm:w-auto"
                  :disabled="actionSubmitting || ticket.status !== 'assigned'"
                  @click="emit('accept-ticket')"
                >
                  {{ actionSubmitting ? 'Updating...' : 'Accept request' }}
                </button>

                <button
                  v-if="viewerRole === 'technician'"
                  class="min-h-11 w-full rounded-full border border-slate-300 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-white disabled:opacity-60 sm:min-h-0 sm:w-auto"
                  :disabled="actionSubmitting || ticket.status !== 'assigned'"
                  @click="emit('reject-ticket')"
                >
                  {{ actionSubmitting ? 'Updating...' : 'Decline request' }}
                </button>
              </div>

              <p v-if="saveError" class="mt-3 text-sm text-rose-700">{{ saveError }}</p>
            </article>

            <article class="rounded-3xl border border-slate-200 bg-white p-4 sm:p-5">
              <div class="mb-4 flex items-center justify-between gap-3">
                <div>
                  <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Conversation</p>
                  <p class="mt-1 text-xs text-slate-500">Use comments to keep the back-and-forth attached to the ticket.</p>
                </div>
              </div>

              <div class="space-y-3">
                <div
                  v-for="comment in ticket.comments || []"
                  :key="comment.id"
                  class="rounded-2xl border px-4 py-3"
                  :class="comment.user.role === viewerRole ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 bg-slate-50 text-slate-800'"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div>
                      <p class="text-sm font-semibold">{{ comment.user.name }}</p>
                      <p class="mt-1 text-xs" :class="comment.user.role === viewerRole ? 'text-slate-300' : 'text-slate-500'">
                        {{ comment.user.role }}
                      </p>
                    </div>
                    <p class="text-xs" :class="comment.user.role === viewerRole ? 'text-slate-300' : 'text-slate-500'">
                      {{ new Date(comment.created_at).toLocaleString() }}
                    </p>
                  </div>
                  <p class="mt-3 whitespace-pre-line text-sm leading-6">{{ comment.body }}</p>
                </div>

                <p v-if="!ticket.comments?.length" class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-5 text-sm text-slate-500">
                  No comments yet.
                </p>
              </div>

              <div class="mt-4">
                <textarea
                  v-model="commentText"
                  rows="4"
                  class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                  :placeholder="resolvedCommentPlaceholder"
                  :disabled="!canComment"
                ></textarea>
                <p v-if="viewerRole === 'technician' && !canComment" class="mt-2 text-xs text-amber-700">
                  Accept this request first to comment on the ticket.
                </p>
                <div class="mt-3 flex justify-stretch sm:justify-end">
                  <button
                    class="min-h-11 w-full rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:opacity-60 sm:min-h-0 sm:w-auto"
                    :disabled="commentSubmitting || !commentText.trim() || !canComment"
                    @click="submitComment"
                  >
                    {{ commentSubmitting ? 'Sending...' : 'Send reply' }}
                  </button>
                </div>
              </div>
            </article>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>
