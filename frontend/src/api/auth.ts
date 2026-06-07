import axios from 'axios'
import type { User } from '../types'

const authApi = axios.create({
  baseURL: '/api/v1/auth',
  headers: { 'Content-Type': 'application/json' },
})

export const authApiCalls = {
  login: (username: string, password: string) =>
    authApi.post<{ access: string; refresh: string; user: User }>('/login/', { username, password }),

  register: (data: {
    username: string
    password: string
    password2: string
    email: string
    company_name?: string
    role?: string
  }) => authApi.post<{ access: string; refresh: string; user: User }>('/register/', data),

  me: (token: string) =>
    authApi.get<User>('/me/', { headers: { Authorization: `Bearer ${token}` } }),
}
