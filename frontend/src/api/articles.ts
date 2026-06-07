import api from './client'
import type { Article, ArticleDetail, PaginatedResponse } from '../types'

export interface ArticleFilters {
  page?: number
  search?: string
  sentiment?: string
  urgency?: string
  status?: string
  source?: number
  fake_score_min?: number
  ordering?: string
}

export const articlesApi = {
  list: (filters: ArticleFilters = {}) =>
    api.get<PaginatedResponse<Article>>('/articles/', { params: filters }),

  get: (id: number) =>
    api.get<ArticleDetail>(`/articles/${id}/`),

  create: (data: { url: string; title?: string; content?: string }) =>
    api.post<Article>('/articles/', data),

  addUrl: (url: string) =>
    api.post('/articles/add_url/', { url }),

  verify: (id: number, isReal: boolean) =>
    api.post(`/articles/${id}/verify/`, { is_real: isReal }),

  reanalyze: (id: number) =>
    api.post(`/articles/${id}/reanalyze/`),
}
