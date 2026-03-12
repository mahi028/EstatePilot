<script setup>
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getUploadUrl } from '@/services/dashboard'

const auth = useAuthStore()
</script>

<template>
  <div class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 shadow-sm sm:p-6">
    <h3 class="mb-4 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Profile</h3>
    <div class="mb-4 flex items-center gap-3">
      <img
        :src="auth.user?.profile_image_path ? getUploadUrl(auth.user.profile_image_path) : 'https://placehold.co/96x96?text=Avatar'"
        alt="Profile"
        class="h-14 w-14 rounded-full border border-[var(--color-border-default)] object-cover"
      />
      <div>
        <p class="text-sm font-semibold text-[var(--color-text-primary)]">{{ auth.user?.name }}</p>
        <p class="text-xs text-[var(--color-text-secondary)] capitalize">{{ auth.user?.role }}</p>
      </div>
    </div>
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

    <RouterLink
      :to="`/profile/${auth.user?.id}`"
      class="mt-4 inline-flex min-h-10 items-center rounded-lg border border-[var(--color-border-default)] px-3 py-2 text-xs font-semibold text-[var(--color-text-primary)] hover:bg-[var(--color-bg-elevated)]"
    >
      Open full profile
    </RouterLink>
  </div>
</template>
