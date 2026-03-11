<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    await auth.fetchProfile()
  } catch {
    error.value = 'Failed to load profile.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="py-10">
    <!-- Loading state -->
    <div v-if="loading" class="text-center text-[var(--color-text-muted)]">Loading...</div>

    <!-- Error state -->
    <div v-else-if="error" class="text-center text-danger-500">{{ error }}</div>

    <!-- Dashboard content -->
    <div v-else>
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-[var(--color-text-primary)]">
          Welcome, {{ auth.user?.name }}
        </h1>
        <p class="mt-1 text-[var(--color-text-secondary)]">Here's your dashboard overview.</p>
      </div>

      <!-- Profile card -->
      <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <div class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-6 shadow-sm">
          <h3 class="mb-4 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Profile</h3>
          <dl class="space-y-3 text-sm">
            <div class="flex justify-between">
              <dt class="text-[var(--color-text-secondary)]">Name</dt>
              <dd class="font-medium text-[var(--color-text-primary)]">{{ auth.user?.name }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-[var(--color-text-secondary)]">Email</dt>
              <dd class="font-medium text-[var(--color-text-primary)]">{{ auth.user?.email }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-[var(--color-text-secondary)]">Role</dt>
              <dd>
                <span class="inline-block rounded-full bg-primary-100 px-2.5 py-0.5 text-xs font-semibold capitalize text-primary-700">
                  {{ auth.user?.role }}
                </span>
              </dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-[var(--color-text-secondary)]">Member since</dt>
              <dd class="font-medium text-[var(--color-text-primary)]">
                {{ auth.user?.created_at ? new Date(auth.user.created_at).toLocaleDateString() : '—' }}
              </dd>
            </div>
          </dl>
        </div>

        <div class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-6 shadow-sm">
          <h3 class="mb-4 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Quick Actions</h3>
          <p class="text-sm text-[var(--color-text-secondary)]">Ticket management and more features coming soon.</p>
        </div>
      </div>
    </div>
  </div>
</template>
