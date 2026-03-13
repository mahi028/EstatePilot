<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import TenantTicketDetail from '@/components/tickets/TenantTicketDetail.vue'
import ManagerTicketDetail from '@/components/tickets/ManagerTicketDetail.vue'
import TechnicianTicketDetail from '@/components/tickets/TechnicianTicketDetail.vue'

const auth = useAuthStore()
const role = computed(() => auth.user?.role)
</script>

<template>
  <div class="space-y-4 py-4 sm:py-6">
    <div>
      <h1 class="text-2xl font-bold text-[var(--color-text-primary)]">Ticket details</h1>
    </div>

    <ManagerTicketDetail v-if="role === 'manager'" />
    <TenantTicketDetail v-else-if="role === 'tenant'" />
    <TechnicianTicketDetail v-else-if="role === 'technician'" />
  </div>
</template>
