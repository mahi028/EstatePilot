<script setup>
import { computed } from 'vue'

const props = defineProps({
  profile: { type: Object, required: true },
  managerProfile: { type: Object, default: null },
  canRemoveManager: { type: Boolean, default: false },
  canRemoveTenant: { type: Boolean, default: false },
  relationshipBusy: { type: Boolean, default: false },
})

const emit = defineEmits(['remove-manager', 'remove-tenant'])

const memberSince = computed(() => {
  if (!props.profile?.created_at) return 'Unknown'
  return new Date(props.profile.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
})

const lastUpdated = computed(() => {
  if (!props.profile?.updated_at) return 'Unknown'
  return new Date(props.profile.updated_at).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
})

const basePriceLabel = computed(() => {
  if (props.profile?.base_price == null || props.profile?.base_price === '') return 'Not set'
  return `$${Number(props.profile.base_price).toFixed(2)}`
})
</script>

<template>
  <article class="details-card">
    <h2 class="card-title">
      <svg class="title-icon" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="7" r="3.5" stroke="currentColor" stroke-width="1.5"/><path d="M3 17c0-3.314 3.134-6 7-6s7 2.686 7 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
      Profile Details
    </h2>

    <!-- Core info grid -->
    <div class="info-grid">
      <div class="info-row">
        <span class="info-label">User ID</span>
        <span class="info-value mono">{{ profile.id }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Email</span>
        <span class="info-value">{{ profile.email || '—' }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Phone</span>
        <span class="info-value">{{ profile.phone || '—' }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Location</span>
        <span class="info-value">{{ profile.location || '—' }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Pincode</span>
        <span class="info-value">{{ profile.pincode || '—' }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Member since</span>
        <span class="info-value">{{ memberSince }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Last updated</span>
        <span class="info-value muted">{{ lastUpdated }}</span>
      </div>

      <!-- Tenant: manager link -->
      <div v-if="profile.role === 'tenant'" class="info-row">
        <span class="info-label">Manager</span>
        <span class="info-value">
          <RouterLink v-if="managerProfile" :to="`/profile/${managerProfile.id}`" class="link">
            {{ managerProfile.name }}
          </RouterLink>
          <span v-else>{{ profile.manager_id || '—' }}</span>
        </span>
      </div>

      <div v-if="canRemoveTenant" class="relationship-actions">
        <button
          class="danger-action"
          :disabled="relationshipBusy"
          @click="emit('remove-tenant', profile)"
        >
          {{ relationshipBusy ? 'Removing...' : 'Remove Tenant' }}
        </button>
      </div>

      <div v-if="canRemoveManager" class="relationship-actions">
        <button
          class="danger-action"
          :disabled="relationshipBusy"
          @click="emit('remove-manager')"
        >
          {{ relationshipBusy ? 'Removing...' : 'Remove Manager' }}
        </button>
      </div>

      <!-- Technician fields -->
      <template v-if="profile.role === 'technician'">
        <div class="info-row">
          <span class="info-label">Headline</span>
          <span class="info-value">{{ profile.technician_headline || '—' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Experience</span>
          <span class="info-value">
            <span v-if="profile.years_experience != null" class="badge-exp">{{ profile.years_experience }} yrs</span>
            <span v-else>—</span>
          </span>
        </div>
        <div class="info-row">
          <span class="info-label">Base price</span>
          <span class="info-value price-value">{{ basePriceLabel }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Service area</span>
          <span class="info-value">{{ profile.service_pincode || '—' }}</span>
        </div>
        <div class="info-row services-row">
          <span class="info-label">Services</span>
          <span class="info-value">
            <span class="services-wrap">
              <span v-for="service in profile.services || []" :key="service.id" class="service-chip" :title="service.description || ''">
                {{ service.label }}
              </span>
              <span v-if="!(profile.services || []).length" class="muted">None selected</span>
            </span>
          </span>
        </div>
      </template>
    </div>

    <!-- Bio -->
    <div class="bio-block">
      <p class="bio-label">About</p>
      <p class="bio-text">{{ profile.bio || 'No bio added yet.' }}</p>
    </div>
  </article>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600&family=DM+Sans:opsz,wght@9..40,400;9..40,500&display=swap');

.details-card {
  font-family: 'DM Sans', sans-serif;
  background: #ffffff;
  border: 1px solid #e8edf4;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 2px 16px rgba(15,23,42,0.06);
}

.card-title {
  font-family: 'Sora', sans-serif;
  font-size: 1.05rem;
  font-weight: 600;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 1.25rem;
}

.title-icon {
  width: 18px;
  height: 18px;
  color: #6366f1;
}

/* Grid */
.info-grid {
  border: 1px solid #f1f5f9;
  border-radius: 10px;
  overflow: hidden;
}

.info-row {
  display: grid;
  grid-template-columns: 130px 1fr;
  gap: 0.75rem;
  padding: 0.65rem 0.85rem;
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.12s;
}

.info-row:last-child { border-bottom: none; }
.info-row:hover { background: #f8fafc; }

.info-label {
  font-size: 0.78rem;
  font-weight: 500;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  align-self: center;
  line-height: 1.4;
}

.info-value {
  font-size: 0.85rem;
  color: #1e293b;
  word-break: break-all;
  align-self: center;
  line-height: 1.5;
}

.mono { font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 0.78rem; color: #475569; }
.muted { color: #94a3b8; }

.price-value {
  font-weight: 600;
  color: #0f172a;
}

.badge-exp {
  background: #eff6ff;
  color: #3b82f6;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  border: 1px solid #bfdbfe;
}

.link {
  color: #6366f1;
  text-decoration: none;
  font-weight: 500;
}
.link:hover { text-decoration: underline; }

.relationship-actions {
  display: flex;
  justify-content: flex-end;
  padding: 0.75rem 0.85rem;
  border-bottom: 1px solid #f1f5f9;
}

.danger-action {
  border: 1px solid #fecaca;
  background: #fff1f2;
  color: #b91c1c;
  border-radius: 8px;
  font-size: 0.76rem;
  font-weight: 600;
  padding: 0.35rem 0.65rem;
  cursor: pointer;
  transition: background 0.12s ease, color 0.12s ease;
}

.danger-action:hover:not(:disabled) {
  background: #ffe4e6;
}

.danger-action:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.services-row { align-items: flex-start; }
.services-wrap { display: flex; flex-wrap: wrap; gap: 0.35rem; padding-top: 2px; }
.service-chip {
  background: #f0f4ff;
  color: #4f46e5;
  border: 1px solid #c7d2fe;
  font-size: 0.72rem;
  font-weight: 500;
  padding: 2px 9px;
  border-radius: 20px;
}

/* Bio */
.bio-block {
  margin-top: 1rem;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  border-radius: 10px;
  padding: 0.9rem 1rem;
}

.bio-label {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #94a3b8;
  margin: 0 0 0.45rem;
}

.bio-text {
  font-size: 0.875rem;
  color: #334155;
  line-height: 1.7;
  white-space: pre-line;
  margin: 0;
}
</style>
