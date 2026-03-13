<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { fetchReceivedInvitations, respondToInvitation } from '@/services/dashboard'

const auth = useAuthStore()
const hasManager = computed(() => !!auth.user?.manager_id)

const invitations = ref([])
const loading = ref(false)
const responding = ref(null) // tracks which invitation id is being responded to

async function loadInvitations() {
  if (hasManager.value) return
  loading.value = true
  try {
    const { data } = await fetchReceivedInvitations({ status: 'pending' })
    invitations.value = data.invitations
  } catch {
    // silently fail — not critical
  } finally {
    loading.value = false
  }
}

async function handleRespond(invitationId, action) {
  responding.value = invitationId
  try {
    await respondToInvitation(invitationId, action)
    invitations.value = invitations.value.filter(i => i.id !== invitationId)
    if (action === 'accept') {
      await auth.fetchProfile() // refresh user to get manager_id
    }
  } catch {
    // keep invitation in list on failure
  } finally {
    responding.value = null
  }
}

onMounted(loadInvitations)
</script>

<template>
  <div class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-6 shadow-sm">
    <h3 class="mb-4 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Your Manager</h3>

    <!-- Has a manager -->
    <div v-if="hasManager">
      <p class="text-sm text-[var(--color-text-secondary)]">
        You are managed by a property manager. They handle your maintenance requests.
      </p>
      <div class="mt-3 flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 text-sm font-bold text-primary-700">
          M
        </div>
        <div>
          <p class="text-sm font-medium text-[var(--color-text-primary)]">Manager Assigned</p>
          <p class="text-xs text-[var(--color-text-muted)]">You can create tickets for maintenance issues.</p>
          <RouterLink
            :to="`/profile/${auth.user?.manager_id}`"
            class="mt-1 inline-block text-xs font-medium text-primary-700 hover:underline"
          >
            Open manager profile
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- No manager -->
    <div v-else>
      <!-- Pending invitations -->
      <div v-if="loading" class="text-sm text-[var(--color-text-muted)]">Loading invitations...</div>

      <div v-else-if="invitations.length" class="space-y-3">
        <p class="text-sm text-[var(--color-text-secondary)]">You have pending invitations from managers:</p>
        <div
          v-for="inv in invitations"
          :key="inv.id"
          class="flex items-center justify-between rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] p-3"
        >
          <div>
            <p class="text-sm font-medium text-[var(--color-text-primary)]">{{ inv.manager.name }}</p>
            <p class="text-xs text-[var(--color-text-muted)]">{{ inv.manager.email }}</p>
          </div>
          <div class="flex gap-2">
            <button
              @click="handleRespond(inv.id, 'accept')"
              :disabled="responding === inv.id"
              class="rounded-lg bg-success-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-success-700 disabled:opacity-50 transition-colors"
            >
              {{ responding === inv.id ? '...' : 'Accept' }}
            </button>
            <button
              @click="handleRespond(inv.id, 'reject')"
              :disabled="responding === inv.id"
              class="rounded-lg bg-danger-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-danger-700 disabled:opacity-50 transition-colors"
            >
              Reject
            </button>
          </div>
        </div>
      </div>

      <!-- No invitations -->
      <div v-else class="flex items-start gap-3 rounded-lg bg-accent-50 p-4">
        <svg class="mt-0.5 h-5 w-5 flex-shrink-0 text-accent-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M12 3a9 9 0 100 18 9 9 0 000-18z" />
        </svg>
        <div>
          <p class="text-sm font-medium text-accent-800">No Manager Assigned</p>
          <p class="mt-1 text-xs text-accent-700">
            You need a manager to create maintenance tickets. Wait for a manager to send you an invitation.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
