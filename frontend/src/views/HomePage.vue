<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const primaryCta = computed(() => (auth.isAuthenticated ? '/dashboard' : '/register'))
const primaryCtaLabel = computed(() => (auth.isAuthenticated ? 'Go to Dashboard' : 'Get Started'))

const coreItems = [
  { title: 'Clear request flow', text: 'Request, review, accept, resolve. Every stage stays visible.' },
  { title: 'Role-based clarity', text: 'Tenants, managers, and technicians each get focused actions.' },
  { title: 'Everything in context', text: 'Comments, images, priority, and status in one ticket thread.' },
]

const roleItems = [
  { role: 'Tenant', text: 'Create requests quickly and follow updates without friction.' },
  { role: 'Manager', text: 'Review queues and send technician requests with full visibility.' },
  { role: 'Technician', text: 'Accept requests before work starts and keep updates structured.' },
]

const steps = [
  'Tenant creates a ticket with details and images.',
  'Manager reviews and sends a technician request.',
  'Technician accepts and begins work.',
  'All updates stay in one readable thread until completion.',
]
</script>

<template>
  <section class="relative overflow-hidden py-8 sm:py-12 lg:py-14">
    <div class="pointer-events-none absolute inset-0 -z-10">
      <div class="absolute -left-20 top-0 h-56 w-56 rounded-full bg-primary-100/70 blur-3xl sm:h-64 sm:w-64"></div>
      <div class="absolute -right-20 bottom-0 h-56 w-56 rounded-full bg-accent-100/70 blur-3xl sm:h-64 sm:w-64"></div>
    </div>

    <article class="rounded-3xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-5 shadow-sm sm:p-7 lg:p-8">
      <p class="text-xs font-semibold uppercase tracking-[0.2em] text-primary-700">EstatePilot</p>
      <h1 class="mt-3 max-w-3xl text-3xl font-bold leading-tight text-[var(--color-text-primary)] sm:text-4xl lg:text-5xl">
        Maintenance ticketing, simplified for modern property teams.
      </h1>
      <p class="mt-4 max-w-2xl text-sm leading-6 text-[var(--color-text-secondary)] sm:text-base">
        A clean, shared workspace for tenants, managers, and technicians. Keep requests, updates, and accountability in one place.
      </p>

      <div class="mt-6 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
        <RouterLink
          :to="primaryCta"
          class="inline-flex min-h-11 items-center justify-center rounded-full bg-primary-600 px-6 py-2 text-sm font-semibold text-white transition hover:bg-primary-700"
        >
          {{ primaryCtaLabel }}
        </RouterLink>
        <RouterLink
          to="/login"
          class="inline-flex min-h-11 items-center justify-center rounded-full border border-[var(--color-border-strong)] bg-[var(--color-bg-input)] px-6 py-2 text-sm font-semibold text-[var(--color-text-primary)] transition hover:bg-[var(--color-bg-elevated)]"
        >
          Sign in
        </RouterLink>
      </div>
    </article>

    <div class="mt-6 grid gap-4 sm:mt-8 md:grid-cols-3">
      <article
        v-for="item in coreItems"
        :key="item.title"
        class="rounded-3xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-5 shadow-sm"
      >
        <h2 class="text-base font-semibold text-[var(--color-text-primary)]">{{ item.title }}</h2>
        <p class="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">{{ item.text }}</p>
      </article>
    </div>

    <div class="mt-6 grid gap-4 sm:mt-8 md:grid-cols-3">
      <article
        v-for="item in roleItems"
        :key="item.role"
        class="rounded-3xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-5 shadow-sm"
      >
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">For {{ item.role }}</p>
        <p class="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">{{ item.text }}</p>
      </article>
    </div>

    <article class="mt-6 rounded-3xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-5 shadow-sm sm:mt-8 sm:p-7">
      <h2 class="text-lg font-semibold text-[var(--color-text-primary)]">How it works</h2>
      <ol class="mt-4 space-y-3">
        <li
          v-for="(step, index) in steps"
          :key="step"
          class="rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] p-4 text-sm text-[var(--color-text-secondary)]"
        >
          <span class="mr-2 font-semibold text-[var(--color-text-primary)]">{{ index + 1 }}.</span>{{ step }}
        </li>
      </ol>
    </article>
  </section>
</template>
