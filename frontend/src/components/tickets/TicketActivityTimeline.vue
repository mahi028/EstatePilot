<script setup>
defineProps({
  logs: { type: Array, default: () => [] },
})

function formatWhen(value) {
  if (!value) return 'Unknown time'
  return new Date(value).toLocaleString()
}
</script>

<template>
  <article class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4">
    <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Activity</p>

    <div v-if="logs.length" class="mt-3 space-y-3">
      <div v-for="log in logs" :key="log.id" class="flex gap-3 rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] p-3">
        <div class="mt-1 h-2.5 w-2.5 rounded-full bg-primary-600"></div>
        <div class="min-w-0 flex-1">
          <p class="text-sm font-medium text-[var(--color-text-primary)]">{{ log.action }}</p>
          <p class="mt-1 text-xs text-[var(--color-text-secondary)]">
            <span v-if="log.user">{{ log.user.name }} ({{ log.user.role }})</span>
            <span v-else>Unknown user</span>
            • {{ formatWhen(log.created_at) }}
          </p>
        </div>
      </div>
    </div>

    <p v-else class="mt-3 text-sm text-[var(--color-text-secondary)]">No activity yet.</p>
  </article>
</template>
