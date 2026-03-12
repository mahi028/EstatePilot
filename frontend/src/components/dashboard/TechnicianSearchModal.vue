<script setup>
import { onMounted, ref } from 'vue'
import { fetchTechnicianServices, searchTechnicians } from '@/services/dashboard'

const props = defineProps({
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'select-technician'])

const searchQuery = ref('')
const selectedServiceId = ref('')
const technicians = ref([])
const services = ref([])
const loading = ref(false)
const searching = ref(false)
const error = ref('')

async function loadServices() {
  try {
    const { data } = await fetchTechnicianServices()
    services.value = data.services
  } catch (err) {
    error.value = 'Failed to load services'
  }
}

async function performSearch() {
  if (!searchQuery.value.trim() && !selectedServiceId.value) {
    technicians.value = []
    return
  }

  searching.value = true
  error.value = ''
  try {
    const { data } = await searchTechnicians(searchQuery.value, selectedServiceId.value)
    technicians.value = data.technicians
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to search technicians'
  } finally {
    searching.value = false
  }
}

function handleSelectTechnician(technician) {
  emit('select-technician', technician)
  closeModal()
}

function closeModal() {
  emit('close')
  searchQuery.value = ''
  selectedServiceId.value = ''
  technicians.value = []
}

onMounted(loadServices)
</script>

<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-end sm:items-center sm:justify-center">
    <div class="fixed inset-0 bg-black/40" @click="closeModal"></div>
    <div class="relative w-full bg-[var(--color-bg-card)] max-h-[100dvh] overflow-y-auto sm:max-h-[92vh] sm:w-full sm:max-w-2xl sm:rounded-[28px]">
      <div class="sticky top-0 flex items-center justify-between border-b border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 backdrop-blur-sm sm:p-6">
        <h2 class="text-lg font-semibold text-[var(--color-text-primary)]">Find Technician & Send Request</h2>
        <button @click="closeModal" class="text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">
          ✕
        </button>
      </div>

      <div class="p-4 sm:p-6">
        <!-- Search Form -->
        <div class="space-y-3 mb-4">
          <div>
            <label class="block text-sm font-medium text-[var(--color-text-primary)] mb-2">Search by name or email</label>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search technicians..."
              class="w-full h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm"
              @input="performSearch"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-[var(--color-text-primary)] mb-2">Filter by service</label>
            <select
              v-model="selectedServiceId"
              class="w-full h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm"
              @change="performSearch"
            >
              <option value="">All services</option>
              <option v-for="service in services" :key="service.id" :value="service.id">
                {{ service.label }}
              </option>
            </select>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="rounded-lg border border-danger-200 bg-danger-50 p-3 text-sm text-danger-700 mb-4">
          {{ error }}
        </div>

        <!-- Loading -->
        <div v-if="searching" class="text-sm text-[var(--color-text-muted)]">Searching technicians...</div>

        <!-- Results -->
        <div v-else-if="technicians.length === 0" class="text-sm text-[var(--color-text-secondary)]">
          No technicians found. Try adjusting your search.
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="technician in technicians"
            :key="technician.id"
            class="rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] p-4 cursor-pointer hover:bg-[var(--color-bg-card)] transition-colors"
            @click="handleSelectTechnician(technician)"
          >
            <div class="flex justify-between items-start gap-3">
              <div class="flex-1 min-w-0">
                <h3 class="font-medium text-[var(--color-text-primary)]">{{ technician.name }}</h3>
                <p class="text-sm text-[var(--color-text-secondary)]">{{ technician.email }}</p>

                <div v-if="technician.technician_headline" class="mt-2 text-sm text-[var(--color-text-primary)]">
                  {{ technician.technician_headline }}
                </div>

                <div class="mt-2 flex flex-wrap gap-2 items-center text-xs text-[var(--color-text-secondary)]">
                  <span v-if="technician.location">📍 {{ technician.location }}</span>
                  <span v-if="technician.phone">📱 {{ technician.phone }}</span>
                  <span v-if="technician.average_rating">⭐ {{ technician.average_rating }}/5 ({{ technician.reviews_count }} reviews)</span>
                </div>

                <div v-if="technician.services?.length" class="mt-2 flex flex-wrap gap-1">
                  <span v-for="service in technician.services" :key="service.id" class="rounded-full bg-primary-100 px-2 py-0.5 text-xs text-primary-700">
                    {{ service.label }}
                  </span>
                </div>
              </div>
              <button
                class="min-h-10 min-w-10 rounded-lg bg-primary-600 px-3 py-2 text-sm font-medium text-white hover:bg-primary-700 whitespace-nowrap"
              >
                Send request
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
