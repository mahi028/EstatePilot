<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import TenantTicketsList from '@/components/tickets/TenantTicketsList.vue'
import ManagerTicketsList from '@/components/tickets/ManagerTicketsList.vue'
import TechnicianTicketsList from '@/components/tickets/TechnicianTicketsList.vue'

const auth = useAuthStore()
const role = computed(() => auth.user?.role)
</script>

<template>
  <div class="space-y-4 py-4 sm:py-6">
    <div>
      <h1 class="text-2xl font-bold text-[var(--color-text-primary)]">Tickets</h1>
      <p class="mt-1 text-sm text-[var(--color-text-secondary)]">Your ticket workspace.</p>
    </div>

    <ManagerTicketsList v-if="role === 'manager'" />
    <TenantTicketsList v-else-if="role === 'tenant'" />
    <TechnicianTicketsList v-else-if="role === 'technician'" />
  </div>
</template>
