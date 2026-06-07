import api from './client'
import type { Source } from '../types'

export const sourcesApi = {
  list: (params?: { source_type?: string; is_active?: boolean }) =>
    api.get<Source[]>('/sources/', { params }),

  get: (id: number) =>
    api.get<Source>(`/sources/${id}/`),

  create: (data: Partial<Source>) =>
    api.post<Source>('/sources/', data),

  update: (id: number, data: Partial<Source>) =>
    api.patch<Source>(`/sources/${id}/`, data),

  delete: (id: number) =>
    api.delete(`/sources/${id}/`),

  crawlNow: (id: number) =>
    api.post(`/sources/${id}/crawl_now/`),

  toggle: (id: number) =>
    api.post(`/sources/${id}/toggle/`),
}
