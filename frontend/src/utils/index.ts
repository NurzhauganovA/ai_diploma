import { formatDistanceToNow, format } from 'date-fns'
import { ru } from 'date-fns/locale'

export function timeAgo(date: string): string {
  try {
    return formatDistanceToNow(new Date(date), { addSuffix: true, locale: ru })
  } catch {
    return date
  }
}

export function formatDate(date: string): string {
  try {
    return format(new Date(date), 'dd.MM.yyyy HH:mm', { locale: ru })
  } catch {
    return date
  }
}

export function fakeScoreColor(score: number | null): string {
  if (score === null) return 'text-gray-500'
  if (score >= 0.75) return 'text-red-400'
  if (score >= 0.5) return 'text-orange-400'
  if (score >= 0.3) return 'text-yellow-400'
  return 'text-green-400'
}

export function fakeScoreBg(score: number | null): string {
  if (score === null) return 'bg-gray-800 text-gray-400'
  if (score >= 0.75) return 'bg-red-900/40 text-red-300 border-red-800/50'
  if (score >= 0.5) return 'bg-orange-900/40 text-orange-300 border-orange-800/50'
  if (score >= 0.3) return 'bg-yellow-900/40 text-yellow-300 border-yellow-800/50'
  return 'bg-green-900/40 text-green-300 border-green-800/50'
}

export function urgencyBadge(urgency: string): string {
  const map: Record<string, string> = {
    critical: 'bg-red-900/50 text-red-300 border border-red-700/50',
    high: 'bg-orange-900/50 text-orange-300 border border-orange-700/50',
    medium: 'bg-yellow-900/50 text-yellow-300 border border-yellow-700/50',
    low: 'bg-gray-800 text-gray-400 border border-gray-700',
  }
  return map[urgency] || map.low
}

export function urgencyLabel(urgency: string): string {
  const map: Record<string, string> = {
    critical: 'Критическая',
    high: 'Высокая',
    medium: 'Средняя',
    low: 'Низкая',
  }
  return map[urgency] || urgency
}

export function sentimentBadge(sentiment: string): string {
  const map: Record<string, string> = {
    positive: 'bg-green-900/40 text-green-300 border border-green-700/40',
    neutral: 'bg-gray-800 text-gray-400 border border-gray-700',
    negative: 'bg-red-900/40 text-red-300 border border-red-700/40',
  }
  return map[sentiment] || map.neutral
}

export function sentimentLabel(sentiment: string): string {
  const map: Record<string, string> = {
    positive: 'Позитивный',
    neutral: 'Нейтральный',
    negative: 'Негативный',
  }
  return map[sentiment] || sentiment
}

export function scorePercent(score: number | null): string {
  if (score === null) return '—'
  return `${Math.round(score * 100)}%`
}
