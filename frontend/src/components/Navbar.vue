<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const mobileOpen = ref(false)
</script>

<template>
  <!-- <nav class="border-b border-[var(--color-border-default)] bg-[var(--color-bg-card)]"> -->
  <nav class="border-b border-[var(--color-border-default)] bg-black">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex h-16 items-center justify-between">

        <!-- Logo / Brand -->
        <RouterLink  v-if="!auth.isAuthenticated" to="/" class="flex items-center gap-2 text-xl font-bold tracking-tight text-primary-600">
          <img src="/favicon.png" alt="EstatePilot" class="h-10 w-auto">
          <img src="/logo-text-transparent.png" alt="EstatePilot" class="h-6 w-auto">
        </RouterLink>
        <RouterLink  v-else to="/dashboard" class="flex items-center gap-2 text-xl font-bold tracking-tight text-primary-600">
          <img src="/favicon.png" alt="EstatePilot" class="h-10 w-auto">
          <img src="/logo-text-transparent.png" alt="EstatePilot" class="h-6 w-auto">
        </RouterLink>


        <!-- Desktop nav links -->
        <div class="hidden items-center gap-3 md:flex">
          <!-- Logged-out links -->
          <template v-if="!auth.isAuthenticated">
            <RouterLink
              to="/login"
              class="rounded-lg px-4 py-2 text-sm font-medium text-slate-200 transition hover:bg-white/10 hover:text-white"
            >
              Log in
            </RouterLink>

            <RouterLink
              to="/register"
              class="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-primary-700"
            >
              Register
            </RouterLink>
          </template>

          <!-- Logged-in links -->
          <template v-else>
            <!-- <RouterLink
              :to="`/profile/${auth.user?.id}`"
              class="rounded-lg px-4 py-2 text-sm font-medium text-[var(--color-text-secondary)] transition hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-primary)]"
            >
              Profile
            </RouterLink> -->

            <!-- <RouterLink
              to="/dashboard"
              class="rounded-lg px-4 py-2 text-sm font-medium text-[var(--color-text-secondary)] transition hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-primary)]"
            >
              Dashboard
            </RouterLink> -->

            <!-- <span class="text-sm text-[var(--color-text-muted)]">{{ auth.user?.name }}</span> -->

            <button
              @click="auth.logout()"
              class="rounded-lg border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 transition hover:bg-rose-500/10 hover:text-rose-300"
            >
              Log out
            </button>
          </template>
        </div>

        <!-- Mobile logged-out actions -->
        <div v-if="!auth.isAuthenticated" class="flex items-center gap-2 md:hidden">
          <RouterLink
            to="/login"
            class="rounded-lg border border-slate-600 px-3 py-1.5 text-xs font-semibold text-slate-100 transition hover:bg-white/10"
          >
            Log in
          </RouterLink>
          <RouterLink
            to="/register"
            class="rounded-lg bg-primary-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-primary-700"
          >
            Register
          </RouterLink>
        </div>

        <!-- Mobile hamburger (authenticated only) -->
        <button
          v-else
          class="inline-flex items-center justify-center rounded-lg p-2 text-slate-200 transition hover:bg-white/10 md:hidden"
          @click="mobileOpen = !mobileOpen"
          aria-label="Toggle menu"
        >
          <svg v-if="!mobileOpen" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Mobile menu -->
    <div v-if="auth.isAuthenticated && mobileOpen" class="border-t border-[var(--color-border-default)] px-4 pb-4 pt-2 md:hidden">
        <!-- <RouterLink
          :to="`/profile/${auth.user?.id}`"
          class="block rounded-lg px-3 py-2 text-sm font-medium text-[var(--color-text-secondary)] transition hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-primary)]"
          @click="mobileOpen = false"
        >
          Profile
        </RouterLink> -->
<!--
        <RouterLink
          to="/dashboard"
          class="block rounded-lg px-3 py-2 text-sm font-medium text-[var(--color-text-secondary)] transition hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-primary)]"
          @click="mobileOpen = false"
        >
          Dashboard
        </RouterLink> -->

        <button
          @click="auth.logout(); mobileOpen = false"
          class="mt-1 block w-full rounded-lg border border-slate-600 px-3 py-2 text-center text-sm font-medium text-slate-200 transition hover:bg-rose-500/10 hover:text-rose-300"
        >
          Log out
        </button>
    </div>
  </nav>
</template>
