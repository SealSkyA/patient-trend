import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getMe } from '../api/auth'
import { listPatients } from '../api/patients'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<any>(null)
  const patients = ref<any[]>([])
  const currentPatient = ref<any>(null)

  function setToken(t: string) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function clearToken() {
    token.value = ''
    currentPatient.value = null
    patients.value = []
    user.value = null
    localStorage.removeItem('token')
  }

  async function loadUser() {
    try {
      const res = await getMe()
      user.value = res.data
    } catch {
      clearToken()
    }
  }

  async function loadPatients() {
    try {
      const res = await listPatients()
      patients.value = res.data
      if (patients.value.length > 0 && !currentPatient.value) {
        currentPatient.value = patients.value[0]
      }
    } catch {
      patients.value = []
    }
  }

  return { token, user, patients, currentPatient, setToken, clearToken, loadUser, loadPatients }
})
