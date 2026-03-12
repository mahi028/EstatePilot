<script setup>
import UserInfoCard from '@/components/dashboard/UserInfoCard.vue'
</script>

<template>
  <div class="space-y-6">
    <UserInfoCard />
    <div class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-6 shadow-sm">
      <h3 class="mb-4 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Technician Dashboard</h3>
      <div class="flex items-center gap-3 rounded-lg bg-info-50 p-4">
        <svg class="h-5 w-5 flex-shrink-0 text-info-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 100 20 10 10 0 000-20z" />
        </svg>
        <div>
          <p class="text-sm font-medium text-info-800">Work assignments coming soon</p>
          <p class="mt-1 text-xs text-info-700">
            Your assigned tickets and work orders will appear here once the feature is available.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
