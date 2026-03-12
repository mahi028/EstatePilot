<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  createTechnicianReview,
  fetchTechnicianServices,
  fetchUserProfile,
  getUploadUrl,
  updateProfile,
  uploadProfileImage,
} from '@/services/dashboard'

const route = useRoute()
const auth = useAuthStore()

const loading = ref(true)
const saving = ref(false)
const uploading = ref(false)
const reviewing = ref(false)
const error = ref('')
const success = ref('')
const profile = ref(null)
const services = ref([])

const editForm = ref({
  name: '',
  phone: '',
  location: '',
  bio: '',
  technician_headline: '',
  years_experience: '',
  base_price: '',
  service_ids: [],
})

const reviewForm = ref({
  rating: 5,
  comment: '',
})

const selectedServiceIds = computed(() => new Set(editForm.value.service_ids))

const userId = computed(() => String(route.params.userId || ''))
const isOwnProfile = computed(() => auth.user?.id && auth.user.id === userId.value)
const canLeaveReview = computed(
  () => profile.value?.role === 'technician' && ['tenant', 'manager'].includes(auth.user?.role)
)

function fillEditForm() {
  editForm.value.name = profile.value?.name || ''
  editForm.value.phone = profile.value?.phone || ''
  editForm.value.location = profile.value?.location || ''
  editForm.value.bio = profile.value?.bio || ''
  if (profile.value?.role === 'technician') {
    editForm.value.technician_headline = profile.value?.technician_headline || ''
    editForm.value.years_experience = profile.value?.years_experience ?? ''
    editForm.value.base_price = profile.value?.base_price ?? ''
    editForm.value.service_ids = (profile.value?.services || []).map((service) => service.id)
  }
}

async function loadProfile() {
  if (!userId.value) return
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    const { data } = await fetchUserProfile(userId.value)
    profile.value = data.user
    fillEditForm()

    // Load services if viewing own technician profile
    if (isOwnProfile.value && profile.value?.role === 'technician' && services.value.length === 0) {
      const { data: servicesData } = await fetchTechnicianServices()
      services.value = servicesData.services
    }
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to load profile.'
  } finally {
    loading.value = false
  }
}

function toggleService(serviceId) {
  if (selectedServiceIds.value.has(serviceId)) {
    editForm.value.service_ids = editForm.value.service_ids.filter((id) => id !== serviceId)
    return
  }
  editForm.value.service_ids = [...editForm.value.service_ids, serviceId]
}

async function saveOwnProfile() {
  if (!isOwnProfile.value) return
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    const payload = {
      name: editForm.value.name,
      phone: editForm.value.phone,
      location: editForm.value.location,
      bio: editForm.value.bio,
    }

    // Add technician fields if profile is technician
    if (profile.value?.role === 'technician') {
      payload.technician_headline = editForm.value.technician_headline
      payload.years_experience = editForm.value.years_experience
      payload.base_price = editForm.value.base_price
      payload.service_ids = editForm.value.service_ids
    }

    const { data } = await updateProfile(payload)
    profile.value = data.user
    auth.user = data.user
    localStorage.setItem('user', JSON.stringify(data.user))
    success.value = 'Profile updated.'
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to update profile.'
  } finally {
    saving.value = false
  }
}

async function uploadOwnProfileImage(event) {
  if (!isOwnProfile.value) return
  const file = event.target.files?.[0]
  if (!file) return

  uploading.value = true
  error.value = ''
  success.value = ''
  try {
    const { data } = await uploadProfileImage(file)
    profile.value = data.user
    auth.user = data.user
    localStorage.setItem('user', JSON.stringify(data.user))
    success.value = 'Profile image updated.'
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to upload image.'
  } finally {
    uploading.value = false
    event.target.value = ''
  }
}

async function submitReview() {
  if (!profile.value || !canLeaveReview.value) return
  reviewing.value = true
  error.value = ''
  success.value = ''
  try {
    const { data } = await createTechnicianReview(profile.value.id, {
      rating: Number(reviewForm.value.rating),
      comment: reviewForm.value.comment,
    })
    profile.value = data.technician
    reviewForm.value.rating = 5
    reviewForm.value.comment = ''
    success.value = 'Review added.'
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to add review.'
  } finally {
    reviewing.value = false
  }
}

watch(() => route.params.userId, loadProfile)
onMounted(loadProfile)
</script>

<template>
  <div class="py-4 sm:py-6">
    <div v-if="loading" class="text-sm text-[var(--color-text-muted)]">Loading profile...</div>

    <div v-else-if="profile" class="space-y-5">
      <section class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 shadow-sm sm:p-6">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-center">
          <img
            :src="profile.profile_image_path ? getUploadUrl(profile.profile_image_path) : 'https://placehold.co/140x140?text=Avatar'"
            alt="Profile"
            class="h-24 w-24 rounded-full border border-[var(--color-border-default)] object-cover"
          />
          <div class="min-w-0 flex-1">
            <h1 class="text-xl font-bold text-[var(--color-text-primary)] sm:text-2xl">{{ profile.name }}</h1>
            <p class="mt-1 text-sm capitalize text-[var(--color-text-secondary)]">{{ profile.role }}</p>
            <p v-if="profile.role === 'technician'" class="mt-1 text-sm text-[var(--color-text-secondary)]">
              Rating: {{ profile.average_rating ?? 'No rating yet' }}
              <span v-if="profile.reviews_count">({{ profile.reviews_count }} reviews)</span>
            </p>
          </div>
          <label v-if="isOwnProfile" class="inline-flex min-h-10 cursor-pointer items-center rounded-lg border border-[var(--color-border-default)] px-3 py-2 text-sm hover:bg-[var(--color-bg-elevated)]">
            {{ uploading ? 'Uploading...' : 'Change image' }}
            <input type="file" accept="image/png,image/jpeg,image/webp" class="hidden" :disabled="uploading" @change="uploadOwnProfileImage" />
          </label>
        </div>
      </section>

      <section class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 shadow-sm sm:p-6">
        <h2 class="mb-3 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Profile Details</h2>
        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <p class="text-xs text-[var(--color-text-secondary)]">Email</p>
            <p class="text-sm font-medium text-[var(--color-text-primary)]">{{ profile.email }}</p>
          </div>
          <div>
            <p class="text-xs text-[var(--color-text-secondary)]">Phone</p>
            <p class="text-sm font-medium text-[var(--color-text-primary)]">{{ profile.phone || '—' }}</p>
          </div>
          <div>
            <p class="text-xs text-[var(--color-text-secondary)]">Location</p>
            <p class="text-sm font-medium text-[var(--color-text-primary)]">{{ profile.location || '—' }}</p>
          </div>
          <div v-if="profile.role === 'technician'">
            <p class="text-xs text-[var(--color-text-secondary)]">Experience</p>
            <p class="text-sm font-medium text-[var(--color-text-primary)]">{{ profile.years_experience ?? '—' }} years</p>
          </div>
          <div v-if="profile.role === 'technician'">
            <p class="text-xs text-[var(--color-text-secondary)]">Base Price</p>
            <p class="text-sm font-medium text-[var(--color-text-primary)]">{{ profile.base_price ?? '—' }}</p>
          </div>
        </div>

        <div class="mt-3">
          <p class="text-xs text-[var(--color-text-secondary)]">Bio</p>
          <p class="mt-1 text-sm text-[var(--color-text-primary)]">{{ profile.bio || 'No bio yet.' }}</p>
        </div>

        <div v-if="profile.role === 'technician'" class="mt-3">
          <p class="text-xs text-[var(--color-text-secondary)]">Services</p>
          <div class="mt-1 flex flex-wrap gap-2">
            <span v-for="service in profile.services || []" :key="service.id" class="rounded-full bg-primary-100 px-2.5 py-1 text-xs font-semibold text-primary-700">
              {{ service.label }}
            </span>
            <span v-if="!(profile.services || []).length" class="text-xs text-[var(--color-text-secondary)]">No services selected yet.</span>
          </div>
        </div>
      </section>

      <section v-if="isOwnProfile" class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 shadow-sm sm:p-6">
        <h2 class="mb-3 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Edit Basic Info</h2>
        <div class="grid gap-3 sm:grid-cols-2">
          <input v-model="editForm.name" type="text" placeholder="Name" class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm" />
          <input v-model="editForm.phone" type="text" placeholder="Phone" class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm" />
          <input v-model="editForm.location" type="text" placeholder="Location" class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm sm:col-span-2" />
          <textarea v-model="editForm.bio" rows="3" placeholder="Bio" class="rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] p-3 text-sm sm:col-span-2"></textarea>
        </div>
      </section>

      <section v-if="isOwnProfile && profile.role === 'technician'" class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 shadow-sm sm:p-6">
        <h2 class="mb-3 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Technician Profile</h2>
        <div class="space-y-3">
          <input v-model="editForm.technician_headline" type="text" placeholder="Headline (e.g., Licensed HVAC specialist)" class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm w-full" />
          <div class="grid gap-3 sm:grid-cols-2">
            <input v-model="editForm.years_experience" type="number" min="0" placeholder="Years of experience" class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm" />
            <input v-model="editForm.base_price" type="number" min="0" step="0.01" placeholder="Base price ($)" class="h-11 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm" />
          </div>
          <div>
            <p class="mb-2 text-sm font-medium text-[var(--color-text-primary)]">Services you provide</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="service in services"
                :key="service.id"
                type="button"
                @click="toggleService(service.id)"
                :class="selectedServiceIds.has(service.id) ? 'bg-primary-600 text-white border-primary-600' : 'bg-[var(--color-bg-input)] text-[var(--color-text-primary)] border-[var(--color-border-default)]'"
                class="rounded-full border px-3 py-1.5 text-xs font-semibold hover:border-primary-600 transition-colors"
              >
                {{ service.label }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <section v-if="isOwnProfile" class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] p-4 shadow-sm">
        <button @click="saveOwnProfile" :disabled="saving" class="w-full min-h-11 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50">
          {{ saving ? 'Saving changes...' : 'Save all changes' }}
        </button>
      </section>

      <section v-if="profile.role === 'technician'" class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-4 shadow-sm sm:p-6">
        <h2 class="mb-3 text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Reviews</h2>
        <div class="space-y-2">
          <article v-for="review in profile.reviews || []" :key="review.id" class="rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] p-3">
            <p class="text-xs font-semibold text-[var(--color-text-primary)]">{{ review.reviewer.name }} ({{ review.reviewer.role }}) • {{ review.rating }}/5</p>
            <p class="mt-1 text-sm text-[var(--color-text-secondary)]">{{ review.comment }}</p>
          </article>
          <p v-if="!(profile.reviews || []).length" class="text-sm text-[var(--color-text-secondary)]">No reviews yet.</p>
        </div>

        <div v-if="canLeaveReview && !isOwnProfile" class="mt-4 space-y-2 border-t border-[var(--color-border-default)] pt-4">
          <p class="text-sm font-medium text-[var(--color-text-primary)]">Leave a review</p>
          <select v-model="reviewForm.rating" class="h-11 w-full rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 text-sm">
            <option v-for="n in [5,4,3,2,1,0]" :key="n" :value="n">{{ n }} star</option>
          </select>
          <textarea v-model="reviewForm.comment" rows="3" placeholder="Share your experience" class="w-full rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] p-3 text-sm"></textarea>
          <button @click="submitReview" :disabled="reviewing" class="min-h-11 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50">
            {{ reviewing ? 'Submitting...' : 'Submit review' }}
          </button>
        </div>
      </section>

      <p v-if="success" class="text-sm text-success-600">{{ success }}</p>
      <p v-if="error" class="text-sm text-danger-500">{{ error }}</p>
    </div>
  </div>
</template>
