import api from './client'
import type { AlertRule, Notification, PaginatedResponse } from '../types'

export const alertsApi = {
  listRules: () =>
    api.get<AlertRule[]>('/alerts/rules/'),

  createRule: (data: Partial<AlertRule>) =>
    api.post<AlertRule>('/alerts/rules/', data),

  updateRule: (id: number, data: Partial<AlertRule>) =>
    api.patch<AlertRule>(`/alerts/rules/${id}/`, data),

  deleteRule: (id: number) =>
    api.delete(`/alerts/rules/${id}/`),

  toggleRule: (id: number) =>
    api.post(`/alerts/rules/${id}/toggle/`),

  listNotifications: (params?: { page?: number }) =>
    api.get<PaginatedResponse<Notification>>('/alerts/notifications/', { params }),

  unreadCount: () =>
    api.get<{ count: number }>('/alerts/notifications/unread_count/'),

  markRead: (id: number) =>
    api.post(`/alerts/notifications/${id}/mark_read/`),

  markAllRead: () =>
    api.post('/alerts/notifications/mark_all_read/'),
}
