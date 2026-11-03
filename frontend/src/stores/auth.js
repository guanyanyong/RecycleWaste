import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi } from '../api'
import { setAccessToken } from '../api/token'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref('')
  const bootstrapped = ref(false)

  const isLoggedIn = computed(() => Boolean(token.value && user.value))
  const permissions = computed(() => user.value?.permissions || [])
  const isAdmin = computed(() => permissions.value.includes('*'))

  function apply(data) {
    token.value = data.access_token
    setAccessToken(data.access_token)
    user.value = data.user
  }

  async function login(username, password) {
    const data = await authApi.login({ username, password })
    apply(data)
    bootstrapped.value = true
    return data
  }

  async function restore() {
    if (bootstrapped.value && token.value) return true
    try {
      const data = await authApi.refresh()
      apply(data)
      bootstrapped.value = true
      return true
    } catch {
      token.value = ''
      user.value = null
      setAccessToken('')
      bootstrapped.value = true
      return false
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      token.value = ''
      user.value = null
      setAccessToken('')
    }
  }

  function hasPerm(perm) {
    if (!perm) return true
    return isAdmin.value || permissions.value.includes(perm)
  }

  return { user, token, isLoggedIn, permissions, isAdmin, login, restore, logout, hasPerm }
})
