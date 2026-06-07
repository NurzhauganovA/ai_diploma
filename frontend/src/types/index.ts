export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: 'admin' | 'analyst' | 'pr_manager'
  company_name: string
  telegram_chat_id: string
  created_at: string
}

export interface Source {
  id: number
  name: string
  url: string
  source_type: 'rss' | 'web' | 'telegram' | 'manual'
  source_type_display: string
  description: string
  is_active: boolean
  crawl_interval: number
  credibility_score: number
  articles_count: number
  last_crawled_at: string | null
  created_at: string
}

export interface Article {
  id: number
  title: string
  summary: string
  url: string
  source_name: string
  language: string
  fake_score: number | null
  sentiment: string
  sentiment_display: string
  sentiment_score: number | null
  toxicity_score: number | null
  urgency: 'low' | 'medium' | 'high' | 'critical'
  topic: string
  status: 'pending' | 'processed' | 'failed'
  threat_level: string
  is_verified: boolean | null
  is_about_company: boolean
  published_at: string | null
  collected_at: string
  keywords?: string[]
  entities?: Array<{ text: string; label: string }>
  shap_data?: {
    top_signals: string[]
    fake_score_components: Record<string, number>
    ai_analyzed?: boolean
    model?: string
    summary?: string
  }
}

export interface ArticleDetail extends Article {
  content: string
  author: string
  image_url: string
  processed_at: string | null
  source: Source | null
}

export interface AlertRule {
  id: number
  name: string
  condition_type: string
  condition_type_display: string
  threshold: number | null
  keyword: string
  urgency_level: string
  sentiment_value: string
  channel: string
  channel_display: string
  is_active: boolean
  notifications_count: number
  last_triggered_at: string | null
  created_at: string
}

export interface Notification {
  id: number
  rule_name: string
  article: Article
  status: string
  channel: string
  message: string
  is_read: boolean
  sent_at: string
}

export interface DashboardStats {
  total_articles: number
  new_today: number
  high_threat_week: number
  fake_count: number
  negative_count: number
  avg_fake_score: number
  reputation_score: number
  unread_alerts: number
  monitored_company?: string
}

export interface TrendPoint {
  date: string
  total: number
  fake: number
  negative: number
  positive: number
  high_threat: number
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
