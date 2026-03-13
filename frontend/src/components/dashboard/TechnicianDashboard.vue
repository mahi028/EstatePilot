<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import UserInfoCard from '@/components/dashboard/UserInfoCard.vue'
import { useAuthStore } from '@/stores/auth'
import {
  fetchMyNotifications,
  markMyNotificationRead,
} from '@/services/dashboard'

const notifications = ref([])
const notificationsLoading = ref(true)
const notificationsError = ref('')
const auth = useAuthStore()

async function loadNotifications() {
  notificationsLoading.value = true
  notificationsError.value = ''
  try {
    const { data } = await fetchMyNotifications()
    notifications.value = data.notifications || []
  } catch (err) {
    notificationsError.value = err.response?.data?.message || 'Failed to load notifications.'
  } finally {
    notificationsLoading.value = false
  }
}

async function markRead(id) {
  try {
    await markMyNotificationRead(id)
    const item = notifications.value.find((n) => n.id === id)
    if (item) item.is_read = true
  } catch {
    // keep UI stable even if a mark-read call fails
  }
}

onMounted(async () => {
  await loadNotifications()
})
</script>

<template>
  <div class="space-y-6">
    <UserInfoCard />

    <div class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 shadow-sm sm:p-6">
      <h3 class="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Quick Links</h3>
      <div class="mt-4 grid gap-3 sm:grid-cols-3">
        <RouterLink to="/technician/tickets/service-area" class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] px-4 py-3 text-sm font-semibold text-[var(--color-text-primary)] hover:border-slate-400">
          Service-area tickets
        </RouterLink>
        <RouterLink to="/technician/tickets/requests" class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] px-4 py-3 text-sm font-semibold text-[var(--color-text-primary)] hover:border-slate-400">
          My ticket requests
        </RouterLink>
        <RouterLink :to="`/profile/${auth.user?.id || ''}`" class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] px-4 py-3 text-sm font-semibold text-[var(--color-text-primary)] hover:border-slate-400">
          My profile
        </RouterLink>
      </div>
    </div>

    <div class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 shadow-sm sm:p-6">
      <div class="flex items-center justify-between gap-3">
        <h3 class="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Notifications</h3>
        <button class="text-xs font-semibold text-primary-700 hover:text-primary-800" @click="loadNotifications">Refresh</button>
      </div>

      <div v-if="notificationsLoading" class="mt-3 text-sm text-[var(--color-text-muted)]">Loading notifications...</div>
      <div v-else-if="notificationsError" class="mt-3 text-sm text-danger-500">{{ notificationsError }}</div>
      <div v-else-if="!notifications.length" class="mt-3 text-sm text-[var(--color-text-secondary)]">No notifications yet.</div>

      <div v-else class="mt-3 space-y-2">
        <article
          v-for="item in notifications"
          :key="item.id"
          class="rounded-xl border px-3 py-3"
          :class="item.is_read ? 'border-[var(--color-border-default)] bg-[var(--color-bg-elevated)]' : 'border-primary-200 bg-primary-50/50'"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-sm text-[var(--color-text-primary)]">{{ item.message }}</p>
              <p class="mt-1 text-xs text-[var(--color-text-secondary)]">{{ new Date(item.created_at).toLocaleString() }}</p>
            </div>
            <button v-if="!item.is_read" class="text-xs font-semibold text-primary-700 hover:text-primary-800" @click="markRead(item.id)">
              Mark read
            </button>
          </div>
        </article>
      </div>
    </div>
  </div>
</template>
