import { useEffect, useState } from 'react'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { Newspaper, AlertTriangle, TrendingDown, Activity } from 'lucide-react'
import { analyticsApi } from '../api/analytics'
import type { DashboardStats, TrendPoint } from '../types'
import { useAuthStore } from '../store/authStore'

const SENTIMENT_COLORS = { positive: '#22c55e', neutral: '#6b7280', negative: '#ef4444' }
const URGENCY_COLORS = { low: '#6b7280', medium: '#eab308', high: '#f97316', critical: '#ef4444' }

function StatCard({
  icon: Icon, label, value, sub, color = 'blue',
}: {
  icon: React.ElementType; label: string; value: string | number; sub?: string; color?: string
}) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    red: 'bg-red-500/10 text-red-400 border-red-500/20',
    green: 'bg-green-500/10 text-green-400 border-green-500/20',
    orange: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  }
  return (
    <div className="card flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center border ${colors[color]}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <div className="text-2xl font-bold text-white">{value}</div>
        <div className="text-sm text-gray-500">{label}</div>
        {sub && <div className="text-xs text-gray-600 mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

function ReputationGauge({ score }: { score: number }) {
  const color = score >= 70 ? '#22c55e' : score >= 45 ? '#eab308' : '#ef4444'
  return (
    <div className="card">
      <div className="text-sm font-medium text-gray-400 mb-4">Индекс репутации</div>
      <div className="flex flex-col items-center py-3">
        <div className="relative w-32 h-32">
          <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
            <circle cx="60" cy="60" r="50" fill="none" stroke="#1f2937" strokeWidth="12" />
            <circle
              cx="60" cy="60" r="50" fill="none"
              stroke={color} strokeWidth="12"
              strokeDasharray={`${score * 3.14} 314`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center rotate-0">
            <span className="text-3xl font-bold" style={{ color }}>{score}</span>
            <span className="text-xs text-gray-500">/ 100</span>
          </div>
        </div>
        <div className="mt-3 text-sm" style={{ color }}>
          {score >= 70 ? 'Хорошая репутация' : score >= 45 ? 'Требует внимания' : 'Критический уровень'}
        </div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [trends, setTrends] = useState<TrendPoint[]>([])
  const [sentiment, setSentiment] = useState<{ positive: number; neutral: number; negative: number } | null>(null)
  const [urgency, setUrgency] = useState<{ low: number; medium: number; high: number; critical: number } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [statsRes, trendsRes, sentimentRes, urgencyRes] = await Promise.all([
          analyticsApi.dashboard(),
          analyticsApi.trends(14),
          analyticsApi.sentiment(30),
          analyticsApi.urgency(30),
        ])
        setStats(statsRes.data)
        setTrends(trendsRes.data)
        setSentiment(sentimentRes.data)
        setUrgency(urgencyRes.data)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  const sentimentData = sentiment
    ? [
        { name: 'Позитивный', value: sentiment.positive, color: SENTIMENT_COLORS.positive },
        { name: 'Нейтральный', value: sentiment.neutral, color: SENTIMENT_COLORS.neutral },
        { name: 'Негативный', value: sentiment.negative, color: SENTIMENT_COLORS.negative },
      ]
    : []

  const urgencyData = urgency
    ? [
        { name: 'Низкая', value: urgency.low, color: URGENCY_COLORS.low },
        { name: 'Средняя', value: urgency.medium, color: URGENCY_COLORS.medium },
        { name: 'Высокая', value: urgency.high, color: URGENCY_COLORS.high },
        { name: 'Критическая', value: urgency.critical, color: URGENCY_COLORS.critical },
      ]
    : []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Дашборд</h1>
          <p className="text-gray-500 mt-1">
            Добро пожаловать, {user?.first_name || user?.username}
            {stats?.monitored_company && (
              <span className="ml-2 text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full">
                Мониторинг: {stats.monitored_company}
              </span>
            )}
          </p>
        </div>
        <div className="text-xs text-gray-600 bg-gray-800/50 border border-gray-700/50 px-3 py-1.5 rounded-lg">
          Обновлено: {new Date().toLocaleTimeString('ru')}
        </div>
      </div>

      {/* Stats grid */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard icon={Newspaper} label="Всего статей" value={stats.total_articles} sub={`+${stats.new_today} сегодня`} color="blue" />
          <StatCard icon={AlertTriangle} label="Фейков обнаружено" value={stats.fake_count} sub="fake score ≥ 60%" color="red" />
          <StatCard icon={TrendingDown} label="Негативных" value={stats.negative_count} sub="за всё время" color="orange" />
          <StatCard icon={Activity} label="Угроз за неделю" value={stats.high_threat_week} sub="высокий + критический" color="purple" />
        </div>
      )}

      {/* Main charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {stats && <ReputationGauge score={stats.reputation_score} />}

        {/* Sentiment pie */}
        <div className="card">
          <div className="text-sm font-medium text-gray-400 mb-4">Тональность (30 дней)</div>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie
                data={sentimentData}
                cx="50%" cy="50%"
                innerRadius={40} outerRadius={70}
                paddingAngle={3}
                dataKey="value"
              >
                {sentimentData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Legend
                formatter={(value) => <span className="text-xs text-gray-400">{value}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Urgency bar */}
        <div className="card">
          <div className="text-sm font-medium text-gray-400 mb-4">Уровни угроз (30 дней)</div>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={urgencyData} barSize={24}>
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {urgencyData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Trends area chart */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="text-sm font-medium text-gray-400">Динамика за 14 дней</div>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-blue-500 inline-block" />Всего</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-red-500 inline-block" />Фейки</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-orange-400 inline-block" />Негатив</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={trends}>
            <defs>
              <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorFake" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <Tooltip
              contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
              labelStyle={{ color: '#9ca3af', fontSize: 11 }}
            />
            <Area type="monotone" dataKey="total" stroke="#3b82f6" fill="url(#colorTotal)" name="Всего" strokeWidth={2} />
            <Area type="monotone" dataKey="fake" stroke="#ef4444" fill="url(#colorFake)" name="Фейки" strokeWidth={2} />
            <Area type="monotone" dataKey="negative" stroke="#f97316" fill="none" name="Негатив" strokeWidth={2} strokeDasharray="4 2" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
