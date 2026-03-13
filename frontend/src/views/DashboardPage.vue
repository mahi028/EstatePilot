<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { fetchMyNotifications, markMyNotificationRead } from '@/services/dashboard'
import ManagedTenantsCard from '@/components/dashboard/ManagedTenantsCard.vue'
import ManagerInfoCard from '@/components/dashboard/ManagerInfoCard.vue'

const auth = useAuthStore()
const loading = ref(true)
const error = ref('')

const notifications = ref([])
const notificationsLoading = ref(true)
const notificationsError = ref('')
const notificationFilters = ref({ q: '', unread: false, page: 1, page_size: 6 })
const notificationPagination = ref({ page: 1, page_size: 6, total: 0, total_pages: 0 })

const links = computed(() => {
  const role = auth.user?.role
  const base = [
    // { to: '/tickets', label: 'Tickets', icon: 'ticket' },
    { to: `/profile/${auth.user?.id || ''}`, label: 'My Profile', icon: 'profile' },
  ]
  if (role === 'manager') return [...base, { to: '/tickets', label: 'Managed Workflow', icon: 'workflow' }]
  if (role === 'technician') return [...base, { to: '/tickets?scope=service-area', label: 'Bidding Queue', icon: 'bid' }]
  return base
})

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

async function loadNotifications() {
  notificationsLoading.value = true
  notificationsError.value = ''
  try {
    const { data } = await fetchMyNotifications({
      q: notificationFilters.value.q || undefined,
      unread: notificationFilters.value.unread || undefined,
      page: notificationFilters.value.page,
      page_size: notificationFilters.value.page_size,
    })
    notifications.value = data.notifications || []
    notificationPagination.value = data.pagination || { page: 1, page_size: notificationFilters.value.page_size, total: 0, total_pages: 0 }
  } catch (err) {
    notificationsError.value = err.response?.data?.message || 'Failed to load notifications.'
  } finally {
    notificationsLoading.value = false
  }
}

function applyNotificationFilters() {
  notificationFilters.value.page = 1
  loadNotifications()
}

function goToNotificationsPage(nextPage) {
  if (nextPage < 1 || nextPage > (notificationPagination.value.total_pages || 1)) return
  notificationFilters.value.page = nextPage
  loadNotifications()
}

async function markRead(id) {
  try {
    await markMyNotificationRead(id)
    const item = notifications.value.find((n) => n.id === id)
    if (item) item.is_read = true
  } catch { /* non-blocking */ }
}

function greeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 18) return 'Good afternoon'
  return 'Good evening'
}

onMounted(async () => {
  try {
    await auth.fetchProfile()
    await loadNotifications()
  } catch {
    error.value = 'Failed to load dashboard.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="dp-shell">
    <!-- Loading -->
    <div v-if="loading" class="dp-loading">
      <div class="dp-sk dp-sk-greeting"></div>
      <div class="dp-sk-row">
        <div class="dp-sk dp-sk-card"></div>
        <div class="dp-sk dp-sk-card"></div>
      </div>
    </div>

    <div v-else-if="error" class="dp-error">{{ error }}</div>

    <div v-else class="dp-content">
      <!-- Greeting banner -->
      <div class="dp-greeting">
        <div>
          <p class="dp-greeting-sub">{{ greeting() }},</p>
          <h1 class="dp-greeting-name">{{ auth.user?.name }}</h1>
        </div>
        <span class="dp-role-pill">{{ auth.user?.role }}</span>
      </div>

      <div class="dp-grid">
        <!-- Quick Links -->
        <section class="dp-card">
          <p class="dp-card-label">Quick Links</p>
          <div class="dp-links-grid">
            <RouterLink
              v-for="item in links"
              :key="item.label"
              :to="item.to"
              class="dp-link"
            >
              <span class="dp-link-label">{{ item.label }}</span>
              <svg class="dp-link-arrow" viewBox="0 0 16 16" fill="none"><path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </RouterLink>
          </div>
        </section>

        <!-- Notifications -->
        <section class="dp-card">
          <div class="dp-notif-header">
            <div class="dp-card-label-row">
              <p class="dp-card-label">Notifications</p>
              <span v-if="unreadCount" class="dp-unread-badge">{{ unreadCount }}</span>
            </div>
            <button class="dp-refresh-btn" @click="loadNotifications">
              <svg viewBox="0 0 16 16" fill="none"><path d="M13.5 3A7 7 0 1 0 14 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M14 3v3h-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
              Refresh
            </button>
          </div>

          <div class="dp-notif-filters">
            <input
              v-model="notificationFilters.q"
              type="text"
              placeholder="Search notifications"
              class="dp-filter-input"
              @keyup.enter="applyNotificationFilters"
            />
            <label class="dp-filter-check">
              <input v-model="notificationFilters.unread" type="checkbox" @change="applyNotificationFilters" />
              Unread only
            </label>
            <button class="dp-filter-apply" @click="applyNotificationFilters">Apply</button>
          </div>

          <div v-if="notificationsLoading" class="dp-notif-loading">
            <div v-for="i in 3" :key="i" class="dp-sk dp-sk-notif"></div>
          </div>
          <p v-else-if="notificationsError" class="dp-notif-err">{{ notificationsError }}</p>
          <p v-else-if="!notifications.length" class="dp-notif-empty">You're all caught up — no notifications yet.</p>

          <div v-else class="dp-notif-list">
            <article
              v-for="item in notifications"
              :key="item.id"
              class="dp-notif-item"
              :class="{ unread: !item.is_read }"
            >
              <div class="dp-notif-dot" v-if="!item.is_read"></div>
              <div class="dp-notif-body">
                <p class="dp-notif-msg">{{ item.message }}</p>
                <p class="dp-notif-time">{{ new Date(item.created_at).toLocaleString() }}</p>
              </div>
              <button v-if="!item.is_read" class="dp-mark-read" @click="markRead(item.id)">
                Mark read
              </button>
            </article>

            <div class="dp-pager-row">
              <span>Page {{ notificationPagination.page || 1 }} of {{ notificationPagination.total_pages || 1 }}</span>
              <div class="dp-pager-actions">
                <button :disabled="(notificationPagination.page || 1) <= 1" @click="goToNotificationsPage((notificationPagination.page || 1) - 1)">Prev</button>
                <button :disabled="(notificationPagination.page || 1) >= (notificationPagination.total_pages || 1)" @click="goToNotificationsPage((notificationPagination.page || 1) + 1)">Next</button>
              </div>
            </div>
          </div>
        </section>
      </div>

      <section v-if="auth.user?.role === 'manager'" class="dp-manager-tools">
        <ManagedTenantsCard />
      </section>

      <section v-if="auth.user?.role === 'tenant'" class="dp-tenant-tools">
        <ManagerInfoCard />
      </section>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700&family=DM+Sans:opsz,wght@9..40,400;9..40,500&display=swap');

.dp-shell {
  font-family: 'DM Sans', sans-serif;
  padding: 1.5rem 0 3rem;
}

/* Loading skeleton */
.dp-loading { display: flex; flex-direction: column; gap: 1.25rem; }
.dp-sk-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; }
.dp-sk {
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
  border-radius: 16px;
}
.dp-sk-greeting { height: 80px; }
.dp-sk-card { height: 200px; }
.dp-sk-notif { height: 56px; margin-bottom: 0.5rem; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

.dp-error { color: #dc2626; font-size: 0.875rem; text-align: center; padding: 2rem 0; }

/* Greeting banner */
.dp-greeting {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
  border-radius: 20px;
  padding: 1.5rem 1.75rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 6px 30px rgba(15,23,42,0.15);
}

.dp-greeting-sub { font-size: 0.85rem; color: #94a3b8; margin: 0 0 0.2rem; }
.dp-greeting-name {
  font-family: 'Sora', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0;
}

.dp-role-pill {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: capitalize;
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(255,255,255,0.1);
  color: #cbd5e1;
  border: 1px solid rgba(255,255,255,0.15);
  white-space: nowrap;
}

/* Grid */
.dp-content { display: flex; flex-direction: column; gap: 0; }
.dp-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
}

.dp-manager-tools,
.dp-tenant-tools {
  margin-top: 1.25rem;
}

/* Cards */
.dp-card {
  background: #fff;
  border: 1px solid #e8edf4;
  border-radius: 16px;
  padding: 1.25rem;
  box-shadow: 0 2px 16px rgba(15,23,42,0.06);
}

.dp-card-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #94a3b8;
  margin: 0 0 1rem;
}

/* Quick links */
.dp-links-grid { display: flex; flex-direction: column; gap: 0.5rem; }
.dp-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.7rem 0.85rem;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  border-radius: 10px;
  text-decoration: none;
  transition: all 0.15s;
}
.dp-link:hover { background: #f0f4ff; border-color: #c7d2fe; }
.dp-link-label { font-size: 0.85rem; font-weight: 600; color: #0f172a; }
.dp-link-arrow { width: 16px; height: 16px; color: #94a3b8; transition: transform 0.15s; }
.dp-link:hover .dp-link-arrow { transform: translateX(3px); color: #6366f1; }

/* Notifications header */
.dp-notif-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; gap: 0.5rem; }
.dp-card-label-row { display: flex; align-items: center; gap: 0.5rem; }
.dp-unread-badge {
  background: #ef4444;
  color: #fff;
  font-size: 0.65rem;
  font-weight: 700;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.dp-refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6366f1;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  font-family: 'DM Sans', sans-serif;
  transition: background 0.12s;
}
.dp-refresh-btn svg { width: 13px; height: 13px; }
.dp-refresh-btn:hover { background: #f0f4ff; }

.dp-notif-loading { display: flex; flex-direction: column; gap: 0.4rem; }
.dp-notif-err { font-size: 0.8rem; color: #dc2626; }
.dp-notif-empty { font-size: 0.83rem; color: #94a3b8; text-align: center; padding: 1rem 0; }

.dp-notif-filters {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.dp-filter-input {
  height: 34px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0 0.6rem;
  font-size: 0.75rem;
}

.dp-filter-check {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  color: #475569;
}

.dp-filter-apply {
  height: 34px;
  border: 1px solid #0f172a;
  background: #0f172a;
  color: #fff;
  border-radius: 8px;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0 0.6rem;
}

.dp-notif-list { display: flex; flex-direction: column; gap: 0.45rem; }

.dp-notif-item {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.7rem 0.8rem;
  border-radius: 10px;
  border: 1px solid #f1f5f9;
  background: #f8fafc;
  transition: border-color 0.12s;
}
.dp-notif-item.unread {
  background: #fdf4ff;
  border-color: #e9d5ff;
}

.dp-notif-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #8b5cf6;
  margin-top: 5px;
  flex-shrink: 0;
}

.dp-notif-body { flex: 1; min-width: 0; }
.dp-notif-msg { font-size: 0.83rem; color: #1e293b; margin: 0 0 0.2rem; line-height: 1.45; }
.dp-notif-time { font-size: 0.72rem; color: #94a3b8; margin: 0; }

.dp-mark-read {
  font-size: 0.72rem;
  font-weight: 600;
  color: #8b5cf6;
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 5px;
  white-space: nowrap;
  font-family: 'DM Sans', sans-serif;
  flex-shrink: 0;
}
.dp-mark-read:hover { background: #f5f3ff; }

.dp-pager-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.72rem;
  color: #64748b;
  border-top: 1px solid #f1f5f9;
  padding-top: 0.55rem;
}

.dp-pager-actions {
  display: flex;
  gap: 0.35rem;
}

.dp-pager-actions button {
  border: 1px solid #cbd5e1;
  background: #fff;
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 0.72rem;
}

.dp-pager-actions button:disabled {
  opacity: 0.45;
}

@media (max-width: 640px) {
  .dp-grid { grid-template-columns: 1fr; }
  .dp-sk-row { grid-template-columns: 1fr; }
  .dp-greeting { flex-direction: column; align-items: flex-start; }
  .dp-notif-filters { grid-template-columns: 1fr; }
}
</style>
