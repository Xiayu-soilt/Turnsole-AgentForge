import { defineStore } from 'pinia'
import api from '../api'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    username: localStorage.getItem('username') || '',
    company: localStorage.getItem('company') || '',
    tenantId: localStorage.getItem('tenantId') || null,
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
  },
  actions: {
    setLogin(data) {
      this.token = data.access_token
      this.username = data.username
      this.company = data.company
      this.tenantId = data.tenant_id
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('username', data.username)
      localStorage.setItem('company', data.company)
      localStorage.setItem('tenantId', data.tenant_id)
    },
    logout() {
      this.token = ''
      this.username = ''
      this.company = ''
      this.tenantId = null
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('company')
      localStorage.removeItem('tenantId')
    },
    async refreshProfile() {
      if (!this.token) return
      try {
        const res = await api.get('/api/auth/me')
        this.username = res.data.username
        this.company = res.data.company
        localStorage.setItem('username', res.data.username)
        localStorage.setItem('company', res.data.company)
      } catch {
        this.logout()
      }
    },
  },
})
