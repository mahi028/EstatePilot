<script setup>
import { ref, onMounted } from 'vue'
import { fetchManagedTenants, searchTenants, sendInvitation, fetchSentInvitations } from '@/services/dashboard'

const tenants = ref([])
const invitations = ref([])
const loading = ref(true)
const error = ref('')

// Search / invite state
const showInviteModal = ref(false)
const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const inviteError = ref('')
const inviteSuccess = ref('')

async function loadData() {
  try {
    const [tenantsRes, invRes] = await Promise.all([
      fetchManagedTenants(),
      fetchSentInvitations({ status: 'pending' }),
    ])
    tenants.value = tenantsRes.data.tenants
    invitations.value = invRes.data.invitations
  } catch {
    error.value = 'Failed to load tenants.'
  } finally {
    loading.value = false
  }
}

async function handleSearch() {
  if (searchQuery.value.trim().length < 2) return
  searching.value = true
  inviteError.value = ''
  inviteSuccess.value = ''
  try {
    const { data } = await searchTenants(searchQuery.value.trim())
    searchResults.value = data.tenants
  } catch {
    inviteError.value = 'Search failed.'
  } finally {
    searching.value = false
  }
}

async function handleInvite(tenantId) {
  inviteError.value = ''
  inviteSuccess.value = ''
  try {
    await sendInvitation(tenantId)
    inviteSuccess.value = 'Invitation sent!'
    searchResults.value = searchResults.value.filter(t => t.id !== tenantId)
    // Refresh pending invitations
    const { data } = await fetchSentInvitations({ status: 'pending' })
    invitations.value = data.invitations
  } catch (err) {
    inviteError.value = err.response?.data?.message || 'Failed to send invitation.'
  }
}

function closeModal() {
  showInviteModal.value = false
  searchQuery.value = ''
  searchResults.value = []
  inviteError.value = ''
  inviteSuccess.value = ''
}

onMounted(loadData)
</script>

<template>
  <div class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-6 shadow-sm">
    <div class="mb-4 flex items-center justify-between">
      <h3 class="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
        Managed Tenants
      </h3>
      <button
        @click="showInviteModal = true"
        class="rounded-lg bg-primary-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-primary-700 transition-colors"
      >
        + Invite Tenant
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-sm text-[var(--color-text-muted)]">Loading...</div>

    <!-- Error -->
    <div v-else-if="error" class="text-sm text-danger-500">{{ error }}</div>

    <!-- Empty state -->
    <div v-else-if="tenants.length === 0 && invitations.length === 0" class="text-sm text-[var(--color-text-secondary)]">
      No tenants yet. Invite your first tenant to get started.
    </div>

    <!-- Tenants list -->
    <div v-else>
      <ul v-if="tenants.length" class="divide-y divide-[var(--color-border-default)]">
        <li v-for="tenant in tenants" :key="tenant.id" class="flex items-center justify-between py-3 first:pt-0 last:pb-0">
          <div>
            <p class="text-sm font-medium text-[var(--color-text-primary)]">{{ tenant.name }}</p>
            <p class="text-xs text-[var(--color-text-muted)]">{{ tenant.email }}</p>
          </div>
          <span class="inline-block rounded-full bg-success-100 px-2 py-0.5 text-xs font-medium text-success-700">Active</span>
        </li>
      </ul>

      <!-- Pending invitations -->
      <div v-if="invitations.length" class="mt-4 border-t border-[var(--color-border-default)] pt-4">
        <p class="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Pending Invitations</p>
        <ul class="space-y-2">
          <li v-for="inv in invitations" :key="inv.id" class="flex items-center justify-between">
            <div>
              <p class="text-sm text-[var(--color-text-primary)]">{{ inv.tenant.name }}</p>
              <p class="text-xs text-[var(--color-text-muted)]">{{ inv.tenant.email }}</p>
            </div>
            <span class="inline-block rounded-full bg-accent-100 px-2 py-0.5 text-xs font-medium text-accent-700">Pending</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- Invite Modal -->
    <Teleport to="body">
      <div v-if="showInviteModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="closeModal">
        <div class="w-full max-w-md rounded-xl bg-[var(--color-bg-card)] p-6 shadow-xl">
          <div class="mb-4 flex items-center justify-between">
            <h4 class="text-lg font-semibold text-[var(--color-text-primary)]">Invite a Tenant</h4>
            <button @click="closeModal" class="text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]">&times;</button>
          </div>

          <!-- Search input -->
          <div class="flex gap-2">
            <input
              v-model="searchQuery"
              @keyup.enter="handleSearch"
              type="text"
              placeholder="Search by name or email..."
              class="flex-1 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
            />
            <button
              @click="handleSearch"
              :disabled="searching || searchQuery.trim().length < 2"
              class="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50 transition-colors"
            >
              {{ searching ? '...' : 'Search' }}
            </button>
          </div>

          <!-- Feedback -->
          <p v-if="inviteError" class="mt-2 text-sm text-danger-500">{{ inviteError }}</p>
          <p v-if="inviteSuccess" class="mt-2 text-sm text-success-600">{{ inviteSuccess }}</p>

          <!-- Results -->
          <ul v-if="searchResults.length" class="mt-4 max-h-60 divide-y divide-[var(--color-border-default)] overflow-y-auto">
            <li v-for="t in searchResults" :key="t.id" class="flex items-center justify-between py-3">
              <div>
                <p class="text-sm font-medium text-[var(--color-text-primary)]">{{ t.name }}</p>
                <p class="text-xs text-[var(--color-text-muted)]">{{ t.email }}</p>
              </div>
              <button
                @click="handleInvite(t.id)"
                class="rounded-lg bg-success-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-success-700 transition-colors"
              >
                Invite
              </button>
            </li>
          </ul>
          <p v-else-if="!searching && searchQuery.length >= 2 && searchResults.length === 0" class="mt-4 text-sm text-[var(--color-text-secondary)]">
            No unassigned tenants found.
          </p>
        </div>
      </div>
    </Teleport>
  </div>
</template>
