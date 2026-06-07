import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bell, CheckCheck, AlertTriangle, ExternalLink } from 'lucide-react'
import { alertsApi } from '../api/alerts'
import type { Notification, PaginatedResponse } from '../types'
import { timeAgo, urgencyBadge, urgencyLabel } from '../utils'

export default function NotificationsPage() {
  const [data, setData] = useState<PaginatedResponse<Notification> | null>(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)

  const load = async () => {
    setLoading(true)
    try {
      const res = await alertsApi.listNotifications({ page })
      setData(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [page])

  const handleMarkRead = async (id: number) => {
    await alertsApi.markRead(id)
    load()
  }

  const handleMarkAllRead = async () => {
    await alertsApi.markAllRead()
    load()
  }

  const unread = data?.results.filter((n) => !n.is_read).length ?? 0
  const totalPages = data ? Math.ceil(data.count / 20) : 1

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Уведомления</h1>
          <p className="text-gray-500 mt-1">{data?.count ?? 0} уведомлений</p>
        </div>
        {unread > 0 && (
          <button onClick={handleMarkAllRead} className="btn-secondary flex items-center gap-2 text-sm">
            <CheckCheck className="w-4 h-4" />
            Прочитать все ({unread})
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        </div>
      ) : data?.results.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Bell className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>Уведомлений пока нет</p>
        </div>
      ) : (
        <div className="space-y-2">
          {data?.results.map((notif) => (
            <div
              key={notif.id}
              className={`card flex items-start gap-4 cursor-pointer transition-all ${
                !notif.is_read ? 'border-blue-600/30 bg-blue-950/10' : ''
              }`}
              onClick={() => !notif.is_read && handleMarkRead(notif.id)}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                !notif.is_read ? 'bg-red-500/20 text-red-400' : 'bg-gray-800 text-gray-600'
              }`}>
                <AlertTriangle className="w-4 h-4" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-medium text-blue-400">{notif.rule_name}</span>
                  {!notif.is_read && (
                    <span className="w-2 h-2 rounded-full bg-blue-400 flex-shrink-0" />
                  )}
                </div>
                <Link
                  to={`/articles/${notif.article.id}`}
                  className="text-sm text-white hover:text-blue-400 font-medium line-clamp-1"
                  onClick={(e) => e.stopPropagation()}
                >
                  {notif.article.title}
                </Link>
                <div className="flex flex-wrap items-center gap-2 mt-1.5">
                  <span className={`badge border ${urgencyBadge(notif.article.urgency)}`}>
                    {urgencyLabel(notif.article.urgency)}
                  </span>
                  {notif.article.fake_score !== null && (
                    <span className="text-xs text-gray-500">
                      Фейк: {Math.round(notif.article.fake_score * 100)}%
                    </span>
                  )}
                  <span className="text-xs text-gray-600">{timeAgo(notif.sent_at)}</span>
                </div>
              </div>

              <a
                href={notif.article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-600 hover:text-gray-400 flex-shrink-0"
                onClick={(e) => e.stopPropagation()}
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary text-sm px-3 py-1.5 disabled:opacity-40">← Назад</button>
          <span className="text-sm text-gray-500">{page} / {totalPages}</span>
          <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="btn-secondary text-sm px-3 py-1.5 disabled:opacity-40">Вперёд →</button>
        </div>
      )}
    </div>
  )
}
