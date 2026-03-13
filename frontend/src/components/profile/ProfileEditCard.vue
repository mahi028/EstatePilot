<script setup>
const props = defineProps({
  profile: { type: Object, required: true },
  services: { type: Array, default: () => [] },
  editForm: { type: Object, required: true },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle-service', 'save'])
</script>

<template>
  <article class="edit-card">
    <h2 class="card-title">
      <svg class="title-icon" viewBox="0 0 20 20" fill="none">
        <path d="M14.5 3.5a2 2 0 0 1 2.83 2.83L6.5 17H3.5v-3L14.5 3.5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
      </svg>
      Edit Profile
    </h2>

    <!-- Base fields -->
    <div class="fields-grid">
      <label class="field">
        <span class="field-label">Full name</span>
        <input v-model="editForm.name" type="text" placeholder="Your name" class="field-input" />
      </label>

      <label class="field">
        <span class="field-label">Phone</span>
        <input v-model="editForm.phone" type="tel" inputmode="numeric" maxlength="20" placeholder="+1 000 000 0000" class="field-input" />
      </label>

      <label class="field">
        <span class="field-label">Pincode</span>
        <input v-model="editForm.pincode" type="text" inputmode="numeric" maxlength="10" placeholder="Pincode" class="field-input" />
      </label>

      <label class="field">
        <span class="field-label">Location</span>
        <input v-model="editForm.location" type="text" placeholder="City, State" class="field-input" />
      </label>

      <label class="field full-width">
        <span class="field-label">Bio</span>
        <textarea v-model="editForm.bio" rows="4" placeholder="Tell clients about yourself…" class="field-textarea"></textarea>
      </label>
    </div>

    <!-- Technician section -->
    <div v-if="profile.role === 'technician'" class="tech-section">
      <p class="section-label">
        <svg class="section-icon" viewBox="0 0 20 20" fill="none"><path d="M10 2L3 6v4c0 4.418 3 7.5 7 8 4-0.5 7-3.582 7-8V6L10 2Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>
        Technician Settings
      </p>

      <label class="field full-width">
        <span class="field-label">Professional headline</span>
        <input v-model="editForm.technician_headline" type="text" placeholder="e.g. Certified HVAC Specialist" class="field-input" />
      </label>

      <div class="fields-grid-inner">
        <label class="field">
          <span class="field-label">Years of experience</span>
          <input v-model="editForm.years_experience" type="number" min="0" placeholder="0" class="field-input" />
        </label>
        <label class="field">
          <span class="field-label">Base price ($)</span>
          <input v-model="editForm.base_price" type="number" min="0" step="0.01" placeholder="0.00" class="field-input" />
        </label>
      </div>

      <label class="field">
        <span class="field-label">Service pincode</span>
        <input v-model="editForm.service_pincode" type="text" inputmode="numeric" maxlength="10" placeholder="Service area pincode" class="field-input" />
      </label>

      <div class="services-picker">
        <p class="field-label">Services you provide</p>
        <div class="services-chips">
          <button
            v-for="service in services"
            :key="service.id"
            type="button"
            :class="['service-chip', editForm.service_ids.includes(service.id) ? 'active' : '']"
            @click="emit('toggle-service', service.id)"
          >
            <svg v-if="editForm.service_ids.includes(service.id)" class="chip-check" viewBox="0 0 12 12" fill="none"><path d="M2 6l3 3 5-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            {{ service.label }}
          </button>
        </div>
      </div>
    </div>

    <button @click="emit('save')" :disabled="saving" class="save-btn">
      <svg v-if="!saving" class="btn-icon" viewBox="0 0 20 20" fill="none"><path d="M4 10l4.5 4.5L16 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <svg v-else class="btn-icon spin" viewBox="0 0 20 20" fill="none"><path d="M10 3a7 7 0 1 0 7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      {{ saving ? 'Saving…' : 'Save changes' }}
    </button>
  </article>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600&family=DM+Sans:opsz,wght@9..40,400;9..40,500&display=swap');

.edit-card {
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

.title-icon { width: 17px; height: 17px; color: #6366f1; }

/* Fields */
.fields-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.85rem;
}

.fields-grid-inner {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.85rem;
  margin-top: 0.85rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.full-width { grid-column: 1 / -1; }

.field-label {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.field-input {
  height: 40px;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  padding: 0 0.75rem;
  font-size: 0.875rem;
  color: #0f172a;
  font-family: 'DM Sans', sans-serif;
  background: #f8fafc;
  transition: border-color 0.15s, box-shadow 0.15s;
  outline: none;
  width: 100%;
  box-sizing: border-box;
}

.field-input:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.12);
  background: #fff;
}

.field-textarea {
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.65rem 0.75rem;
  font-size: 0.875rem;
  color: #0f172a;
  font-family: 'DM Sans', sans-serif;
  background: #f8fafc;
  resize: vertical;
  min-height: 90px;
  transition: border-color 0.15s, box-shadow 0.15s;
  outline: none;
  width: 100%;
  box-sizing: border-box;
}

.field-textarea:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.12);
  background: #fff;
}

/* Technician block */
.tech-section {
  margin-top: 1.25rem;
  background: #f8f9ff;
  border: 1.5px solid #e0e7ff;
  border-radius: 12px;
  padding: 1rem 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.section-label {
  font-family: 'Sora', sans-serif;
  font-size: 0.82rem;
  font-weight: 600;
  color: #4f46e5;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0;
}

.section-icon { width: 15px; height: 15px; }

/* Service chips */
.services-picker { display: flex; flex-direction: column; gap: 0.5rem; }
.services-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; }

.service-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border: 1.5px solid #c7d2fe;
  background: #fff;
  color: #4f46e5;
  font-family: 'DM Sans', sans-serif;
}

.service-chip:hover { background: #eef2ff; }
.service-chip.active {
  background: #4f46e5;
  color: #fff;
  border-color: #4f46e5;
  box-shadow: 0 2px 8px rgba(79,70,229,0.25);
}

.chip-check { width: 11px; height: 11px; }

/* Save button */
.save-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 1.25rem;
  width: 100%;
  height: 42px;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  font-family: 'DM Sans', sans-serif;
  transition: opacity 0.18s, transform 0.18s;
  box-shadow: 0 3px 14px rgba(79,70,229,0.35);
}

.save-btn:hover:not(:disabled) { opacity: 0.92; transform: translateY(-1px); }
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-icon { width: 16px; height: 16px; }
@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 0.8s linear infinite; }

@media (max-width: 480px) {
  .fields-grid, .fields-grid-inner { grid-template-columns: 1fr; }
  .full-width { grid-column: auto; }
}
</style>
