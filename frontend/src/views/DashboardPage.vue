<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import ManagerDashboard from '@/components/dashboard/ManagerDashboard.vue'
import TenantDashboard from '@/components/dashboard/TenantDashboard.vue'
import TechnicianDashboard from '@/components/dashboard/TechnicianDashboard.vue'

const auth = useAuthStore()
const loading = ref(true)
const error = ref('')

const role = computed(() => auth.user?.role)

onMounted(async () => {
  try {
    await auth.fetchProfile()
  } catch {
    error.value = 'Failed to load profile.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="py-4 sm:py-6 lg:py-8">
    <!-- Loading state -->
    <div v-if="loading" class="text-center text-[var(--color-text-muted)]">Loading...</div>

    <!-- Error state -->
    <div v-else-if="error" class="text-center text-danger-500">{{ error }}</div>

    <!-- Dashboard content -->
    <div v-else>
      <div class="mb-4 sm:mb-6 lg:mb-8">
        <h1 class="text-2xl font-bold text-[var(--color-text-primary)] sm:text-3xl">
          Welcome, {{ auth.user?.name }}
        </h1>
        <p class="mt-1 text-sm text-[var(--color-text-secondary)] sm:text-base">Here's your dashboard overview.</p>
      </div>

      <ManagerDashboard v-if="role === 'manager'" />
      <TenantDashboard v-else-if="role === 'tenant'" />
      <TechnicianDashboard v-else-if="role === 'technician'" />
    </div>
  </div>
</template>
