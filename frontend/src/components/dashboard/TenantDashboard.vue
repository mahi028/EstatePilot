<script setup>
import UserInfoCard from '@/components/dashboard/UserInfoCard.vue'
import ManagerInfoCard from '@/components/dashboard/ManagerInfoCard.vue'
import TenantTicketsCard from '@/components/dashboard/TenantTicketsCard.vue'
</script>

<template>
  <div class="space-y-6">
    <div class="grid gap-6 lg:grid-cols-2">
      <UserInfoCard />
      <ManagerInfoCard />
    </div>
    <TenantTicketsCard />
  </div>
</template>
