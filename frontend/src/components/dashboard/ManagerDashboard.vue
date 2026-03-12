<script setup>
import UserInfoCard from '@/components/dashboard/UserInfoCard.vue'
import ManagedTenantsCard from '@/components/dashboard/ManagedTenantsCard.vue'
import ManagedTicketsCard from '@/components/dashboard/ManagedTicketsCard.vue'
</script>

<template>
  <div class="space-y-6">
    <div class="grid gap-6 lg:grid-cols-3">
      <UserInfoCard />
      <div class="lg:col-span-2">
        <ManagedTenantsCard />
      </div>
    </div>
    <ManagedTicketsCard />
  </div>
</template>
