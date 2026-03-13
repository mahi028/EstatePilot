<script setup>
import { computed } from 'vue'
import { getUploadUrl } from '@/services/dashboard'

const props = defineProps({
  profile: { type: Object, required: true },
  isOwnProfile: { type: Boolean, default: false },
  isEditing: { type: Boolean, default: false },
  uploading: { type: Boolean, default: false },
})

const emit = defineEmits(['upload-image', 'start-edit', 'stop-edit'])

const profileImageSrc = computed(() => {
  if (props.profile?.profile_image_path) return getUploadUrl(props.profile.profile_image_path)
  return 'https://placehold.co/240x240?text=Profile'
})

const joinedLabel = computed(() => {
  if (!props.profile?.created_at) return 'Unknown'
  return new Date(props.profile.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
})

const roleColor = computed(() => {
  const map = { technician: 'role-tech', manager: 'role-mgr', tenant: 'role-tenant' }
  return map[props.profile?.role] || 'role-default'
})
</script>

<template>
  <section class="profile-hero">
    <div class="hero-inner">
      <!-- Avatar block -->
      <div class="avatar-wrap">
        <img :src="profileImageSrc" alt="Profile photo" class="avatar-img" />
        <span class="avatar-ring" />
        <span :class="['role-badge', roleColor]">{{ profile.role }}</span>
      </div>

      <!-- Info block -->
      <div class="hero-info">
        <div class="hero-name-row">
          <h1 class="hero-name">{{ profile.name }}</h1>
          <span v-if="profile.technician_headline" class="hero-headline">{{ profile.technician_headline }}</span>
        </div>

        <div class="hero-meta">
          <span class="meta-item">
            <svg class="meta-icon" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/><path d="M8 4.5v3.75l2.5 1.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            Member since {{ joinedLabel }}
          </span>
          <span v-if="profile.location" class="meta-item">
            <svg class="meta-icon" viewBox="0 0 16 16" fill="none"><path d="M8 1.5C5.515 1.5 3.5 3.515 3.5 6c0 3.75 4.5 8.5 4.5 8.5S12.5 9.75 12.5 6c0-2.485-2.015-4.5-4.5-4.5Z" stroke="currentColor" stroke-width="1.5"/><circle cx="8" cy="6" r="1.5" stroke="currentColor" stroke-width="1.25"/></svg>
            {{ profile.location }}
          </span>
          <span v-if="profile.role === 'technician'" class="meta-item rating-item">
            <svg class="meta-icon star-icon" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1l1.85 3.75L14 5.5l-3 2.92.71 4.13L8 10.5l-3.71 1.95.71-4.13L2 5.5l4.15-.75L8 1Z"/></svg>
            {{ profile.average_rating ?? 'N/A' }}
            <span class="rating-count">({{ profile.reviews_count || 0 }} reviews)</span>
          </span>
        </div>

        <!-- Actions -->
        <div v-if="isOwnProfile" class="hero-actions">
          <template v-if="!isEditing">
            <button type="button" class="btn-primary" @click="emit('start-edit')">
              <svg viewBox="0 0 16 16" fill="none" class="btn-icon"><path d="M11.5 2.5a1.414 1.414 0 0 1 2 2L5 13H3v-2L11.5 2.5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>
              Edit profile
            </button>
          </template>
          <template v-else>
            <label class="btn-secondary">
              <svg viewBox="0 0 16 16" fill="none" class="btn-icon"><rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/><circle cx="6" cy="6.5" r="1.5" stroke="currentColor" stroke-width="1.25"/><path d="M2.5 12L6 8.5l2.5 2.5 2-2 3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
              {{ uploading ? 'Uploading…' : 'Change photo' }}
              <input type="file" accept="image/png,image/jpeg,image/webp" class="hidden" :disabled="uploading" @change="emit('upload-image', $event)" />
            </label>
            <button type="button" class="btn-ghost" @click="emit('stop-edit')">
              Close editor
            </button>
          </template>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;1,9..40,400&display=swap');

.profile-hero {
  font-family: 'DM Sans', sans-serif;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #1a2744 100%);
  border-radius: 20px;
  padding: 2px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.22), 0 1.5px 0 rgba(255,255,255,0.06) inset;
}

.hero-inner {
  background: linear-gradient(135deg, #0f172a 0%, #1b2a45 100%);
  border-radius: 18px;
  padding: 2rem 2rem 1.75rem;
  display: flex;
  align-items: flex-start;
  gap: 1.75rem;
  position: relative;
  overflow: hidden;
}

.hero-inner::before {
  content: '';
  position: absolute;
  top: -60px;
  right: -60px;
  width: 240px;
  height: 240px;
  background: radial-gradient(circle, rgba(99,179,237,0.07) 0%, transparent 70%);
  pointer-events: none;
}

/* Avatar */
.avatar-wrap {
  position: relative;
  flex-shrink: 0;
}

.avatar-img {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  object-fit: cover;
  display: block;
  position: relative;
  z-index: 1;
}

.avatar-ring {
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  background: linear-gradient(135deg, #38bdf8, #6366f1, #a78bfa);
  z-index: 0;
}

.avatar-img { box-shadow: 0 0 0 3px #0f172a; }

.role-badge {
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.6rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 2px 8px;
  border-radius: 20px;
  white-space: nowrap;
  z-index: 2;
}

.role-tech { background: #0ea5e9; color: #fff; }
.role-mgr  { background: #8b5cf6; color: #fff; }
.role-tenant { background: #10b981; color: #fff; }
.role-default { background: #475569; color: #fff; }

/* Info */
.hero-info {
  flex: 1;
  min-width: 0;
}

.hero-name-row {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.75rem;
  margin-bottom: 0.6rem;
}

.hero-name {
  font-family: 'Sora', sans-serif;
  font-size: 1.55rem;
  font-weight: 700;
  color: #f1f5f9;
  line-height: 1.2;
  margin: 0;
}

.hero-headline {
  font-size: 0.85rem;
  color: #94a3b8;
  font-style: italic;
}

/* Meta row */
.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1.25rem;
  margin-bottom: 1.25rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  color: #94a3b8;
}

.meta-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.rating-item { color: #fbbf24; }
.star-icon { color: #fbbf24; }
.rating-count { color: #94a3b8; font-size: 0.75rem; }

/* Actions */
.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.btn-primary, .btn-secondary, .btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 1rem;
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.18s ease;
  font-family: 'DM Sans', sans-serif;
  border: none;
}

.btn-primary {
  background: linear-gradient(135deg, #38bdf8, #6366f1);
  color: #fff;
  box-shadow: 0 2px 12px rgba(99,102,241,0.35);
}
.btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }

.btn-secondary {
  background: rgba(255,255,255,0.07);
  color: #cbd5e1;
  border: 1px solid rgba(255,255,255,0.1);
  cursor: pointer;
}
.btn-secondary:hover { background: rgba(255,255,255,0.12); }

.btn-ghost {
  background: transparent;
  color: #64748b;
  border: 1px solid rgba(255,255,255,0.06);
}
.btn-ghost:hover { color: #94a3b8; background: rgba(255,255,255,0.04); }

.btn-icon { width: 14px; height: 14px; }
.hidden { display: none; }

@media (max-width: 480px) {
  .hero-inner { flex-direction: column; align-items: center; text-align: center; padding: 1.5rem 1.25rem; }
  .hero-name-row { justify-content: center; }
  .hero-meta { justify-content: center; }
  .hero-actions { justify-content: center; }
}
</style>
