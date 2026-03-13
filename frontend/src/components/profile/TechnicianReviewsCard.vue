<script setup>
import { computed } from 'vue'

const props = defineProps({
  profile: { type: Object, required: true },
  canLeaveReview: { type: Boolean, default: false },
  isOwnProfile: { type: Boolean, default: false },
  reviewForm: { type: Object, required: true },
  reviewing: { type: Boolean, default: false },
})

const emit = defineEmits(['submit-review'])

const selectedRating = computed(() => Number(props.reviewForm.rating || 0))

function setRating(value) {
  props.reviewForm.rating = value
}

function ratingLabel(r) {
  const map = { 1: 'Poor', 2: 'Fair', 3: 'Good', 4: 'Great', 5: 'Excellent' }
  return map[r] || ''
}

function reviewerInitials(name) {
  return (name || '?').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
}

function avatarColor(name) {
  const colors = ['#6366f1','#0ea5e9','#10b981','#f59e0b','#ef4444','#8b5cf6']
  let h = 0
  for (const c of (name || '')) h = (h * 31 + c.charCodeAt(0)) % colors.length
  return colors[h]
}
</script>

<template>
  <article v-if="profile.role === 'technician'" class="reviews-card">
    <!-- Header -->
    <div class="card-header">
      <h2 class="card-title">
        <svg class="title-icon" viewBox="0 0 20 20" fill="none">
          <path d="M10 2l2.39 4.84L18 7.64l-4 3.9.94 5.5L10 14.4l-4.94 2.64L6 11.54 2 7.64l5.61-.8L10 2Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
        </svg>
        Reviews
      </h2>
      <div class="header-stats">
        <span class="stat-avg">{{ profile.average_rating ?? '—' }}</span>
        <div class="stat-stars">
          <svg v-for="s in 5" :key="s" class="star" :class="s <= Math.round(profile.average_rating || 0) ? 'filled' : ''" viewBox="0 0 12 12" fill="currentColor">
            <path d="M6 1l1.35 2.74L10.5 4.2l-2.25 2.19.53 3.09L6 8.12 3.22 9.48l.53-3.09L1.5 4.2l3.15-.46L6 1Z"/>
          </svg>
        </div>
        <span class="stat-count">{{ (profile.reviews || []).length }} reviews</span>
      </div>
    </div>

    <!-- Review list -->
    <div class="reviews-list">
      <div v-for="review in profile.reviews || []" :key="review.id" class="review-item">
        <div class="reviewer-avatar" :style="{ background: avatarColor(review.reviewer.name) }">
          {{ reviewerInitials(review.reviewer.name) }}
        </div>
        <div class="review-body">
          <div class="review-top">
            <p class="reviewer-name">{{ review.reviewer.name }}</p>
            <div class="review-stars">
              <svg v-for="s in 5" :key="s" class="star sm" :class="s <= review.rating ? 'filled' : ''" viewBox="0 0 12 12" fill="currentColor">
                <path d="M6 1l1.35 2.74L10.5 4.2l-2.25 2.19.53 3.09L6 8.12 3.22 9.48l.53-3.09L1.5 4.2l3.15-.46L6 1Z"/>
              </svg>
              <span class="review-score">{{ review.rating }}/5</span>
            </div>
          </div>
          <span class="reviewer-role">{{ review.reviewer.role }}</span>
          <p v-if="review.comment" class="review-comment">{{ review.comment }}</p>
        </div>
      </div>

      <div v-if="!(profile.reviews || []).length" class="empty-state">
        <svg viewBox="0 0 40 40" fill="none" class="empty-icon"><circle cx="20" cy="20" r="18" stroke="#e2e8f0" stroke-width="2"/><path d="M20 11l2.7 5.47L28.4 17.3l-4.2 4.09 1 5.81L20 24.27l-5.2 2.93 1-5.81-4.2-4.09 5.7-.83L20 11Z" stroke="#cbd5e1" stroke-width="1.5" stroke-linejoin="round"/></svg>
        <p>No reviews yet</p>
      </div>
    </div>

    <!-- Leave a review form -->
    <div v-if="canLeaveReview && !isOwnProfile" class="review-form">
      <p class="form-title">Leave a review</p>

      <div class="rating-selector">
        <div class="star-buttons">
          <button
            v-for="star in 5"
            :key="star"
            type="button"
            class="star-btn"
            :class="star <= selectedRating ? 'lit' : ''"
            @click="setRating(star)"
            :aria-label="`Rate ${star} stars`"
          >★</button>
        </div>
        <span class="rating-text">{{ ratingLabel(selectedRating) }}</span>
      </div>

      <textarea
        v-model="reviewForm.comment"
        rows="3"
        placeholder="Share your experience with this technician…"
        class="review-textarea"
      ></textarea>

      <button @click="emit('submit-review')" :disabled="reviewing" class="submit-btn">
        <svg v-if="!reviewing" class="btn-icon" viewBox="0 0 20 20" fill="none"><path d="M3 10l14-7-7 14V10H3Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>
        <svg v-else class="btn-icon spin" viewBox="0 0 20 20" fill="none"><path d="M10 3a7 7 0 1 0 7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        {{ reviewing ? 'Submitting…' : 'Submit review' }}
      </button>
    </div>
  </article>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600&family=DM+Sans:opsz,wght@9..40,400;9..40,500&display=swap');

.reviews-card {
  font-family: 'DM Sans', sans-serif;
  background: #ffffff;
  border: 1px solid #e8edf4;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 2px 16px rgba(15,23,42,0.06);
}

/* Header */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.card-title {
  font-family: 'Sora', sans-serif;
  font-size: 1.05rem;
  font-weight: 600;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
}

.title-icon { width: 17px; height: 17px; color: #f59e0b; }

.header-stats {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.stat-avg {
  font-family: 'Sora', sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  color: #0f172a;
}

.stat-stars { display: flex; gap: 1px; }
.stat-count { font-size: 0.78rem; color: #94a3b8; margin-left: 2px; }

/* Stars */
.star { width: 12px; height: 12px; color: #e2e8f0; }
.star.sm { width: 11px; height: 11px; }
.star.filled { color: #f59e0b; }

/* Reviews list */
.reviews-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.review-item {
  display: flex;
  gap: 0.85rem;
  padding: 0.85rem;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  border-radius: 12px;
  transition: border-color 0.15s;
}

.review-item:hover { border-color: #e0e7ff; }

.reviewer-avatar {
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.02em;
}

.review-body { flex: 1; min-width: 0; }

.review-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-bottom: 0.15rem;
}

.reviewer-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.review-stars {
  display: flex;
  align-items: center;
  gap: 2px;
}

.review-score {
  font-size: 0.72rem;
  font-weight: 600;
  color: #94a3b8;
  margin-left: 4px;
}

.reviewer-role {
  font-size: 0.72rem;
  text-transform: capitalize;
  color: #94a3b8;
  display: block;
  margin-bottom: 0.5rem;
}

.review-comment {
  font-size: 0.83rem;
  color: #475569;
  line-height: 1.55;
  margin: 0;
}

/* Empty */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem 1rem;
  color: #94a3b8;
  font-size: 0.85rem;
}
.empty-icon { width: 40px; height: 40px; }

/* Review form */
.review-form {
  margin-top: 1.25rem;
  border-top: 1px solid #f1f5f9;
  padding-top: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.form-title {
  font-family: 'Sora', sans-serif;
  font-size: 0.9rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.rating-selector {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.star-buttons { display: flex; gap: 2px; }

.star-btn {
  font-size: 1.5rem;
  line-height: 1;
  background: none;
  border: none;
  cursor: pointer;
  color: #e2e8f0;
  transition: color 0.12s, transform 0.12s;
  padding: 0;
}
.star-btn:hover, .star-btn.lit { color: #f59e0b; }
.star-btn:hover { transform: scale(1.15); }

.rating-text {
  font-size: 0.8rem;
  font-weight: 600;
  color: #f59e0b;
  min-width: 60px;
}

.review-textarea {
  width: 100%;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.65rem 0.75rem;
  font-size: 0.875rem;
  color: #0f172a;
  font-family: 'DM Sans', sans-serif;
  background: #f8fafc;
  resize: vertical;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.review-textarea:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
  background: #fff;
}

.submit-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0 1.25rem;
  height: 40px;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  color: #fff;
  border: none;
  border-radius: 9px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  font-family: 'DM Sans', sans-serif;
  transition: opacity 0.18s, transform 0.18s;
  box-shadow: 0 3px 12px rgba(245,158,11,0.35);
  align-self: flex-start;
}
.submit-btn:hover:not(:disabled) { opacity: 0.9; transform: translateY(-1px); }
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-icon { width: 15px; height: 15px; }
@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 0.8s linear infinite; }
</style>
