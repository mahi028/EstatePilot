<script setup>
import TechnicianServiceAreaList from '@/components/tickets/TechnicianServiceAreaList.vue'
</script>

<template>
  <div class="space-y-4 py-4 sm:py-6">
    <div class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 sm:p-5">
      <h1 class="text-2xl font-bold text-[var(--color-text-primary)]">Service Area Opportunities</h1>
      <p class="mt-1 text-sm text-[var(--color-text-secondary)]">Browse open tickets in your service area and pick up jobs that match your expertise.</p>
    </div>

    <TechnicianServiceAreaList />
  </div>
</template>
