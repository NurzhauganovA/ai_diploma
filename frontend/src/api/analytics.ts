import api from './client'
import type { DashboardStats, TrendPoint } from '../types'

export const analyticsApi = {
  dashboard: () =>
    api.get<DashboardStats>('/analytics/dashboard/'),

  trends: (days = 7) =>
    api.get<TrendPoint[]>('/analytics/trends/', { params: { days } }),

  sentiment: (days = 30) =>
    api.get<{ positive: number; neutral: number; negative: number }>('/analytics/sentiment/', { params: { days } }),

  topSources: (days = 30) =>
    api.get('/analytics/sources/', { params: { days } }),

  topics: (days = 30) =>
    api.get<Array<{ topic: string; count: number }>>('/analytics/topics/', { params: { days } }),

  urgency: (days = 30) =>
    api.get<{ low: number; medium: number; high: number; critical: number }>('/analytics/urgency/', { params: { days } }),

  reputation: (days = 30) =>
    api.get<Array<{ date: string; reputation_score: number }>>('/analytics/reputation/', { params: { days } }),
}
