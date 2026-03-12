<script setup>
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
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
</template>
