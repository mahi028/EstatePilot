<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import TenantTicketsList from '@/components/tickets/TenantTicketsList.vue'
import ManagerTicketsList from '@/components/tickets/ManagerTicketsList.vue'
import TechnicianTicketsList from '@/components/tickets/TechnicianTicketsList.vue'

const auth = useAuthStore()
const role = computed(() => auth.user?.role)
const subtitle = computed(() => {
  if (role.value === 'manager') return 'Review tenant workload, prioritize requests, and assign technicians.'
  if (role.value === 'tenant') return 'Create and track maintenance requests with clear status updates.'
  if (role.value === 'technician') return 'Track your assigned work, progress updates, and completed jobs.'
  return 'Your ticket workspace.'
})
</script>

<template>
  <div class="space-y-4 py-4 sm:py-6">
    <div class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 sm:p-5">
      <h1 class="text-2xl font-bold text-[var(--color-text-primary)]">Tickets</h1>
      <p class="mt-1 text-sm text-[var(--color-text-secondary)]">{{ subtitle }}</p>
    </div>

    <ManagerTicketsList v-if="role === 'manager'" />
    <TenantTicketsList v-else-if="role === 'tenant'" />
    <TechnicianTicketsList v-else-if="role === 'technician'" />
  </div>
</template>
