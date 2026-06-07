import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Search, Plus, RefreshCw, ExternalLink, CheckCircle, XCircle } from 'lucide-react'
import { articlesApi } from '../api/articles'
import type { Article, PaginatedResponse } from '../types'
import { timeAgo, urgencyBadge, urgencyLabel, sentimentBadge, sentimentLabel, fakeScoreBg } from '../utils'

const PAGE_SIZE = 20

export default function ArticlesPage() {
  const [data, setData] = useState<PaginatedResponse<Article> | null>(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({
    search: '', sentiment: '', urgency: '', status: '',
  })
  const [addUrl, setAddUrl] = useState('')
  const [addingUrl, setAddingUrl] = useState(false)
  const [addMsg, setAddMsg] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page }
      if (filters.search) params.search = filters.search
      if (filters.sentiment) params.sentiment = filters.sentiment
      if (filters.urgency) params.urgency = filters.urgency
      if (filters.status) params.status = filters.status
      const res = await articlesApi.list(params)
      setData(res.data)
    } finally {
      setLoading(false)
    }
  }, [page, filters])

  useEffect(() => { load() }, [load])

  const handleAddUrl = async () => {
    if (!addUrl.trim()) return
    setAddingUrl(true)
    setAddMsg('')
    try {
      await articlesApi.addUrl(addUrl.trim())
      setAddMsg('URL добавлен в очередь анализа!')
      setAddUrl('')
      setTimeout(() => { setAddMsg(''); load() }, 2000)
    } catch {
      setAddMsg('Ошибка при добавлении URL')
    } finally {
      setAddingUrl(false)
    }
  }

  const totalPages = data ? Math.ceil(data.count / PAGE_SIZE) : 1

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Лента угроз</h1>
          <p className="text-gray-500 mt-1">{data?.count ?? 0} публикаций в базе</p>
        </div>
        <button onClick={load} className="btn-secondary flex items-center gap-2 text-sm">
          <RefreshCw className="w-4 h-4" />
          Обновить
        </button>
      </div>

      {/* Add URL */}
      <div className="card">
        <div className="text-sm font-medium text-gray-400 mb-3">Добавить URL для анализа</div>
        <div className="flex gap-2">
          <input
            type="url"
            value={addUrl}
            onChange={(e) => setAddUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddUrl()}
            placeholder="https://example.com/article"
            className="input flex-1"
          />
          <button onClick={handleAddUrl} disabled={addingUrl} className="btn-primary flex items-center gap-2 whitespace-nowrap">
            <Plus className="w-4 h-4" />
            {addingUrl ? 'Добавляю...' : 'Анализировать'}
          </button>
        </div>
        {addMsg && (
          <p className={`text-sm mt-2 ${addMsg.startsWith('Ошибка') ? 'text-red-400' : 'text-green-400'}`}>
            {addMsg}
          </p>
        )}
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-48">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={filters.search}
              onChange={(e) => { setFilters({ ...filters, search: e.target.value }); setPage(1) }}
              placeholder="Поиск по заголовку..."
              className="input pl-9"
            />
          </div>
          <select
            value={filters.sentiment}
            onChange={(e) => { setFilters({ ...filters, sentiment: e.target.value }); setPage(1) }}
            className="input w-40"
          >
            <option value="">Тональность</option>
            <option value="positive">Позитивная</option>
            <option value="neutral">Нейтральная</option>
            <option value="negative">Негативная</option>
          </select>
          <select
            value={filters.urgency}
            onChange={(e) => { setFilters({ ...filters, urgency: e.target.value }); setPage(1) }}
            className="input w-40"
          >
            <option value="">Угроза</option>
            <option value="critical">Критическая</option>
            <option value="high">Высокая</option>
            <option value="medium">Средняя</option>
            <option value="low">Низкая</option>
          </select>
          <select
            value={filters.status}
            onChange={(e) => { setFilters({ ...filters, status: e.target.value }); setPage(1) }}
            className="input w-40"
          >
            <option value="">Статус</option>
            <option value="processed">Обработана</option>
            <option value="pending">Ожидает</option>
            <option value="failed">Ошибка</option>
          </select>
        </div>
      </div>

      {/* Articles list */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="space-y-2">
          {data?.results.map((article) => (
            <ArticleRow key={article.id} article={article} />
          ))}
          {data?.results.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <Search className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>Публикации не найдены</p>
            </div>
          )}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="btn-secondary text-sm px-3 py-1.5 disabled:opacity-40"
          >
            ← Назад
          </button>
          <span className="text-sm text-gray-500">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="btn-secondary text-sm px-3 py-1.5 disabled:opacity-40"
          >
            Вперёд →
          </button>
        </div>
      )}
    </div>
  )
}

function ArticleRow({ article }: { article: Article }) {
  return (
    <div className="card hover:border-gray-700 transition-colors">
      <div className="flex items-start gap-4">
        {/* Fake score */}
        <div className={`px-2.5 py-1 rounded-lg text-xs font-bold border flex-shrink-0 ${fakeScoreBg(article.fake_score)}`}>
          {article.fake_score !== null ? `${Math.round(article.fake_score * 100)}%` : '—'}
          <div className="text-[10px] font-normal opacity-70">фейк</div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start gap-2">
            <Link
              to={`/articles/${article.id}`}
              className="font-medium text-white hover:text-blue-400 transition-colors line-clamp-2 flex-1"
            >
              {article.title}
            </Link>
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-600 hover:text-gray-400 flex-shrink-0 mt-0.5"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
          {article.summary && (
            <p className="text-gray-500 text-sm mt-1 line-clamp-1">{article.summary}</p>
          )}
          <div className="flex flex-wrap items-center gap-2 mt-2">
            <span className={`badge border ${urgencyBadge(article.urgency)}`}>
              {urgencyLabel(article.urgency)}
            </span>
            <span className={`badge border ${sentimentBadge(article.sentiment)}`}>
              {sentimentLabel(article.sentiment)}
            </span>
            {article.topic && (
              <span className="badge bg-gray-800 text-gray-400 border border-gray-700">{article.topic}</span>
            )}
            {article.source_name && (
              <span className="text-xs text-gray-600">{article.source_name}</span>
            )}
            <span className="text-xs text-gray-700 ml-auto">{timeAgo(article.collected_at)}</span>
          </div>
        </div>

        {/* Verification status */}
        {article.is_verified !== null && (
          <div className="flex-shrink-0">
            {article.is_verified
              ? <CheckCircle className="w-4 h-4 text-green-500" />
              : <XCircle className="w-4 h-4 text-red-500" />
            }
          </div>
        )}
      </div>
    </div>
  )
}
