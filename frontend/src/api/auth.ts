import api from './client'

export interface LoginData {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  phone?: string
  password: string
}

export function login(data: LoginData) {
  return api.post('/api/auth/login', data)
}

export function register(data: RegisterData) {
  return api.post('/api/auth/register', data)
}

export function getMe() {
  return api.get('/api/auth/me')
}
