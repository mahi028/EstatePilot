<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  createTechnicianReview,
  fetchTechnicianServices,
  fetchUserProfile,
  updateProfile,
  uploadProfileImage,
} from '@/services/dashboard'
import ProfileHero from '@/components/profile/ProfileHero.vue'
import ProfileDetailsCard from '@/components/profile/ProfileDetailsCard.vue'
import ProfileEditCard from '@/components/profile/ProfileEditCard.vue'
import TechnicianReviewsCard from '@/components/profile/TechnicianReviewsCard.vue'

const route = useRoute()
const auth = useAuthStore()

const loading = ref(true)
const saving = ref(false)
const uploading = ref(false)
const reviewing = ref(false)
const isEditing = ref(false)
const error = ref('')
const success = ref('')
const profile = ref(null)
const managerProfile = ref(null)
const services = ref([])

const editForm = ref({
  name: '',
  phone: '',
  pincode: '',
  location: '',
  bio: '',
  technician_headline: '',
  years_experience: '',
  base_price: '',
  service_pincode: '',
  service_ids: [],
})

const reviewForm = ref({
  rating: 5,
  comment: '',
})

const selectedServiceIds = computed(() => new Set(editForm.value.service_ids))
const userId = computed(() => String(route.params.userId || ''))
const isOwnProfile = computed(() => auth.user?.id && auth.user.id === userId.value)
const canLeaveReview = computed(() => profile.value?.role === 'technician' && ['tenant', 'manager'].includes(auth.user?.role))

function fillEditForm() {
  editForm.value.name = profile.value?.name || ''
  editForm.value.phone = profile.value?.phone || ''
  editForm.value.pincode = profile.value?.pincode || ''
  editForm.value.location = profile.value?.location || ''
  editForm.value.bio = profile.value?.bio || ''
  if (profile.value?.role === 'technician') {
    editForm.value.technician_headline = profile.value?.technician_headline || ''
    editForm.value.years_experience = profile.value?.years_experience ?? ''
    editForm.value.base_price = profile.value?.base_price ?? ''
    editForm.value.service_pincode = profile.value?.service_pincode || ''
    editForm.value.service_ids = (profile.value?.services || []).map((service) => service.id)
  } else {
    editForm.value.technician_headline = ''
    editForm.value.years_experience = ''
    editForm.value.base_price = ''
    editForm.value.service_pincode = ''
    editForm.value.service_ids = []
  }
}

async function loadProfile() {
  if (!userId.value) return
  loading.value = true
  isEditing.value = false
  error.value = ''
  success.value = ''

  try {
    const { data } = await fetchUserProfile(userId.value)
    profile.value = data.user
    managerProfile.value = null

    if (isOwnProfile.value) {
      auth.setUser(data.user)
    }

    fillEditForm()

    if (data.user?.role === 'tenant' && data.user?.manager_id) {
      try {
        const managerResp = await fetchUserProfile(data.user.manager_id)
        managerProfile.value = managerResp.data.user
      } catch {
        managerProfile.value = null
      }
    }

    if (isOwnProfile.value && data.user?.role === 'technician' && services.value.length === 0) {
      const { data: servicesData } = await fetchTechnicianServices()
      services.value = servicesData.services || []
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
      pincode: editForm.value.pincode,
      location: editForm.value.location,
      bio: editForm.value.bio,
    }

    if (profile.value?.role === 'technician') {
      payload.technician_headline = editForm.value.technician_headline
      payload.years_experience = editForm.value.years_experience
      payload.base_price = editForm.value.base_price
      payload.service_pincode = editForm.value.service_pincode
      payload.service_ids = editForm.value.service_ids
    }

    await updateProfile(payload)
    const own = await auth.fetchProfile()
    profile.value = own
    fillEditForm()
    success.value = 'Profile updated.'
  } catch (err) {
    error.value = err.response?.data?.message || err.response?.data?.errors?.name?.[0] || 'Failed to update profile.'
  } finally {
    saving.value = false
  }
}

function startEditing() {
  if (!isOwnProfile.value) return
  isEditing.value = true
}

function stopEditing() {
  isEditing.value = false
}

async function uploadOwnProfileImage(event) {
  if (!isOwnProfile.value) return
  const file = event.target.files?.[0]
  if (!file) return

  uploading.value = true
  error.value = ''
  success.value = ''

  try {
    await uploadProfileImage(file)
    const own = await auth.fetchProfile()
    profile.value = own
    fillEditForm()
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
  <div class="mx-auto max-w-6xl py-4 sm:py-6">
    <div v-if="loading" class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-6 text-sm text-[var(--color-text-muted)] shadow-sm">
      Loading profile...
    </div>

    <div v-else-if="profile" class="space-y-6">
      <ProfileHero
        :profile="profile"
        :is-own-profile="isOwnProfile"
        :is-editing="isEditing"
        :uploading="uploading"
        @start-edit="startEditing"
        @stop-edit="stopEditing"
        @upload-image="uploadOwnProfileImage"
      />

      <div class="grid gap-6 xl:grid-cols-[1.55fr_1fr]">
        <div class="space-y-6">
          <ProfileDetailsCard
            :profile="profile"
            :manager-profile="managerProfile"
          />

          <TechnicianReviewsCard
            :profile="profile"
            :can-leave-review="canLeaveReview"
            :is-own-profile="isOwnProfile"
            :review-form="reviewForm"
            :reviewing="reviewing"
            @submit-review="submitReview"
          />
        </div>

        <div class="space-y-4">
          <ProfileEditCard
            v-if="isOwnProfile && isEditing"
            :profile="profile"
            :services="services"
            :edit-form="editForm"
            :saving="saving"
            @toggle-service="toggleService"
            @save="saveOwnProfile"
          />

          <article v-if="success" class="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-medium text-emerald-700">
            {{ success }}
          </article>
          <article v-if="error" class="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm font-medium text-rose-700">
            {{ error }}
          </article>
        </div>
      </div>
    </div>
  </div>
</template>
