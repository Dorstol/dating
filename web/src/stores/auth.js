import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/client'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)

  const isAuthenticated = computed(() => !!token.value)

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  async function loginTelegram(initData) {
    const { data } = await api.post('/auth/telegram', { init_data: initData })
    setToken(data.access_token)
    return data
  }

  async function loginEmail(email, password) {
    const params = new URLSearchParams()
    params.append('username', email)
    params.append('password', password)
    const { data } = await api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    setToken(data.access_token)
    return data
  }

  async function fetchUser() {
    const { data } = await api.get('/users/me')
    user.value = data
    return data
  }

  return {
    token,
    user,
    isAuthenticated,
    setToken,
    logout,
    loginTelegram,
    loginEmail,
    fetchUser,
  }
})
