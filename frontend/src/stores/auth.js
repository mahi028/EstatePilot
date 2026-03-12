import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('user')))
  const accessToken = ref(localStorage.getItem('access_token'))

  const isAuthenticated = computed(() => !!accessToken.value)

  function _saveTokens(data) {
    accessToken.value = data.access_token
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
  }

  function _saveUser(u) {
    user.value = u
    localStorage.setItem('user', JSON.stringify(u))
  }

  async function register(payload) {
    const { data } = await api.post('/auth/register', payload)
    _saveTokens(data)
    _saveUser(data.user)
    return data
  }

  async function login(payload) {
    const { data } = await api.post('/auth/login', payload)
    _saveTokens(data)
    _saveUser(data.user)
    return data
  }

  async function fetchProfile() {
    const { data } = await api.get('/auth/profile')
    _saveUser(data.user)
    return data.user
  }

  function logout() {
    user.value = null
    accessToken.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    router.push({ name: 'login' })
  }

  return { user, accessToken, isAuthenticated, register, login, fetchProfile, logout }
})
