<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({
  email: '',
  password: '',
})

const loading = ref(false)
const errors = ref({})
const serverError = ref('')

async function handleLogin() {
  errors.value = {}
  serverError.value = ''
  loading.value = true

  try {
    await auth.login(form)
    router.push({ name: 'dashboard' })
  } catch (err) {
    const data = err.response?.data
    if (data?.errors) {
      errors.value = data.errors
    } else {
      serverError.value = data?.message || 'Login failed. Please try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-[calc(100vh-4rem)] items-center justify-center py-8">
    <div class="w-full max-w-md rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-8 shadow-sm">
      <h2 class="mb-6 text-center text-2xl font-bold text-[var(--color-text-primary)]">Welcome back</h2>

      <!-- Server error banner -->
      <div v-if="serverError" class="mb-4 rounded-lg bg-danger-50 p-3 text-sm text-danger-600">
        {{ serverError }}
      </div>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <!-- Email -->
        <div>
          <label for="email" class="mb-1 block text-sm font-medium text-[var(--color-text-secondary)]">Email</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            required
            class="w-full rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 py-2 text-sm text-[var(--color-text-primary)] outline-none transition focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
          />
          <p v-if="errors.email" class="mt-1 text-xs text-danger-500">{{ errors.email[0] }}</p>
        </div>

        <!-- Password -->
        <div>
          <label for="password" class="mb-1 block text-sm font-medium text-[var(--color-text-secondary)]">Password</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            required
            class="w-full rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-input)] px-3 py-2 text-sm text-[var(--color-text-primary)] outline-none transition focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
          />
          <p v-if="errors.password" class="mt-1 text-xs text-danger-500">{{ errors.password[0] }}</p>
        </div>

        <!-- Submit -->
        <button
          type="submit"
          :disabled="loading"
          class="w-full rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-primary-700 disabled:opacity-50"
        >
          {{ loading ? 'Logging in...' : 'Log in' }}
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-[var(--color-text-muted)]">
        Don't have an account?
        <RouterLink to="/register" class="font-medium text-primary-600 hover:text-primary-500">Register</RouterLink>
      </p>
    </div>
  </div>
</template>
