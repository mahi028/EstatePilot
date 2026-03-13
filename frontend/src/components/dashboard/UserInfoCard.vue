<script setup>
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getUploadUrl } from '@/services/dashboard'

const auth = useAuthStore()

function roleColor(role) {
  const map = { technician: '#0ea5e9', manager: '#8b5cf6', tenant: '#10b981' }
  return map[role] || '#64748b'
}

function initials(name) {
  return (name || '?').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
}
</script>

<template>
  <div class="uic-card">
    <p class="uic-section-label">Your Profile</p>

    <div class="uic-hero">
      <div class="uic-avatar-wrap">
        <img
          v-if="auth.user?.profile_image_path"
          :src="getUploadUrl(auth.user.profile_image_path)"
          alt="Avatar"
          class="uic-avatar-img"
        />
        <div v-else class="uic-avatar-fallback" :style="{ background: roleColor(auth.user?.role) }">
          {{ initials(auth.user?.name) }}
        </div>
        <span class="uic-avatar-ring" />
      </div>
      <div class="uic-hero-info">
        <p class="uic-name">{{ auth.user?.name }}</p>
        <span class="uic-role-chip" :style="{ background: roleColor(auth.user?.role) + '18', color: roleColor(auth.user?.role), borderColor: roleColor(auth.user?.role) + '40' }">
          {{ auth.user?.role }}
        </span>
      </div>
    </div>

    <dl class="uic-dl">
      <div class="uic-row">
        <dt>Email</dt>
        <dd>{{ auth.user?.email || '—' }}</dd>
      </div>
      <div class="uic-row">
        <dt>Role</dt>
        <dd class="capitalize">{{ auth.user?.role || '—' }}</dd>
      </div>
      <div class="uic-row">
        <dt>Member since</dt>
        <dd>{{ auth.user?.created_at ? new Date(auth.user.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—' }}</dd>
      </div>
    </dl>

    <RouterLink :to="`/profile/${auth.user?.id}`" class="uic-profile-link">
      <svg viewBox="0 0 16 16" fill="none" class="uic-link-icon"><circle cx="8" cy="6" r="3" stroke="currentColor" stroke-width="1.5"/><path d="M2 14c0-3.314 2.686-5 6-5s6 1.686 6 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
      View full profile
    </RouterLink>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700&family=DM+Sans:opsz,wght@9..40,400;9..40,500&display=swap');

.uic-card {
  font-family: 'DM Sans', sans-serif;
  background: #fff;
  border: 1px solid #e8edf4;
  border-radius: 16px;
  padding: 1.25rem 1.25rem 1rem;
  box-shadow: 0 2px 16px rgba(15,23,42,0.06);
}

.uic-section-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #94a3b8;
  margin: 0 0 1rem;
}

.uic-hero {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  margin-bottom: 1.1rem;
}

.uic-avatar-wrap { position: relative; flex-shrink: 0; }

.uic-avatar-img,
.uic-avatar-fallback {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  object-fit: cover;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 700;
  color: #fff;
  position: relative;
  z-index: 1;
  box-shadow: 0 0 0 3px #fff;
}

.uic-avatar-ring {
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  background: linear-gradient(135deg, #38bdf8, #8b5cf6);
  z-index: 0;
}

.uic-hero-info { min-width: 0; }
.uic-name {
  font-family: 'Sora', sans-serif;
  font-size: 0.95rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.3rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.uic-role-chip {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: capitalize;
  padding: 2px 9px;
  border-radius: 20px;
  border: 1px solid;
  display: inline-block;
}

.uic-dl { border: 1px solid #f1f5f9; border-radius: 10px; overflow: hidden; margin-bottom: 1rem; }
.uic-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem 0.8rem;
  border-bottom: 1px solid #f1f5f9;
  font-size: 0.8rem;
  transition: background 0.12s;
}
.uic-row:hover { background: #f8fafc; }
.uic-row:last-child { border-bottom: none; }
dt { color: #94a3b8; font-weight: 500; flex-shrink: 0; }
dd { color: #1e293b; font-weight: 500; text-align: right; word-break: break-all; margin: 0; }

.uic-profile-link {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #6366f1;
  text-decoration: none;
  padding: 0.4rem 0.75rem;
  border-radius: 8px;
  border: 1px solid #c7d2fe;
  background: #f0f4ff;
  transition: background 0.15s;
}
.uic-profile-link:hover { background: #e0e7ff; }
.uic-link-icon { width: 14px; height: 14px; }
</style>
