import { useEffect, useState } from 'react'
import { Plus, Trash2, RefreshCw, Globe, Rss, MessageCircle, ToggleLeft, ToggleRight } from 'lucide-react'
import { sourcesApi } from '../api/sources'
import type { Source } from '../types'
import { timeAgo } from '../utils'

const TYPE_ICONS: Record<string, React.ElementType> = {
  rss: Rss,
  web: Globe,
  telegram: MessageCircle,
  manual: Globe,
}

const TYPE_LABELS: Record<string, string> = {
  rss: 'RSS', web: 'Веб-сайт', telegram: 'Telegram', manual: 'Ручной',
}

interface AddSourceForm {
  name: string; url: string; source_type: 'rss' | 'web' | 'telegram' | 'manual'; crawl_interval: number; credibility_score: number; description: string
}

const defaultForm: AddSourceForm = {
  name: '', url: '', source_type: 'rss', crawl_interval: 1800, credibility_score: 0.7, description: '',
}

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<AddSourceForm>(defaultForm)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const res = await sourcesApi.list()
      setSources(Array.isArray(res.data) ? res.data : (res.data as { results: Source[] }).results ?? [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await sourcesApi.create(form)
      setForm(defaultForm)
      setShowForm(false)
      setMsg('Источник добавлен!')
      setTimeout(() => setMsg(''), 3000)
      load()
    } catch {
      setMsg('Ошибка при добавлении источника')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Удалить источник "${name}"?`)) return
    await sourcesApi.delete(id)
    load()
  }

  const handleToggle = async (id: number) => {
    await sourcesApi.toggle(id)
    load()
  }

  const handleCrawl = async (id: number, name: string) => {
    await sourcesApi.crawlNow(id)
    setMsg(`Обход "${name}" запущен`)
    setTimeout(() => setMsg(''), 3000)
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Источники</h1>
          <p className="text-gray-500 mt-1">{sources.length} источников настроено</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Добавить
        </button>
      </div>

      {msg && (
        <div className={`px-4 py-2.5 rounded-lg text-sm ${msg.startsWith('Ошибка') ? 'bg-red-900/30 text-red-300 border border-red-700/40' : 'bg-green-900/30 text-green-300 border border-green-700/40'}`}>
          {msg}
        </div>
      )}

      {/* Add form */}
      {showForm && (
        <div className="card border-blue-600/30">
          <div className="text-sm font-medium text-white mb-4">Новый источник</div>
          <form onSubmit={handleAdd} className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Название *</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" required placeholder="RIA Новости" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">URL *</label>
              <input value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} className="input" required placeholder="https://example.com/rss" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Тип источника</label>
              <select value={form.source_type} onChange={(e) => setForm({ ...form, source_type: e.target.value as AddSourceForm['source_type'] })} className="input">
                <option value="rss">RSS лента</option>
                <option value="web">Веб-сайт</option>
                <option value="telegram">Telegram</option>
                <option value="manual">Ручной ввод</option>
              </select>

            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Интервал обхода (сек)</label>
              <input type="number" value={form.crawl_interval} onChange={(e) => setForm({ ...form, crawl_interval: Number(e.target.value) })} className="input" min={60} max={86400} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Рейтинг доверия (0–1)</label>
              <input type="number" value={form.credibility_score} onChange={(e) => setForm({ ...form, credibility_score: Number(e.target.value) })} className="input" min={0} max={1} step={0.05} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Описание</label>
              <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="input" placeholder="Опционально" />
            </div>
            <div className="col-span-2 flex gap-3 pt-1">
              <button type="submit" disabled={saving} className="btn-primary">{saving ? 'Сохраняю...' : 'Сохранить'}</button>
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Отмена</button>
            </div>
          </form>
        </div>
      )}

      {/* Sources grid */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sources.map((source) => {
            const Icon = TYPE_ICONS[source.source_type] || Globe
            return (
              <div key={source.id} className={`card flex flex-col gap-3 ${!source.is_active ? 'opacity-60' : ''}`}>
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gray-800 border border-gray-700 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-5 h-5 text-gray-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-white text-sm">{source.name}</span>
                      <span className="badge bg-gray-800 text-gray-500 border border-gray-700 text-[10px]">
                        {TYPE_LABELS[source.source_type]}
                      </span>
                      {!source.is_active && (
                        <span className="badge bg-gray-800 text-gray-600 border border-gray-700 text-[10px]">Отключён</span>
                      )}
                    </div>
                    <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-xs text-gray-600 hover:text-gray-400 truncate block">{source.url}</a>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="bg-gray-800/50 rounded-lg p-2">
                    <div className="text-sm font-semibold text-white">{source.articles_count}</div>
                    <div className="text-[10px] text-gray-600">статей</div>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-2">
                    <div className="text-sm font-semibold text-white">{Math.round(source.credibility_score * 100)}%</div>
                    <div className="text-[10px] text-gray-600">доверие</div>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-2">
                    <div className="text-sm font-semibold text-white">{Math.round(source.crawl_interval / 60)} м</div>
                    <div className="text-[10px] text-gray-600">интервал</div>
                  </div>
                </div>

                {source.last_crawled_at && (
                  <div className="text-xs text-gray-600">Последний обход: {timeAgo(source.last_crawled_at)}</div>
                )}

                <div className="flex gap-2 pt-1 border-t border-gray-800">
                  <button onClick={() => handleCrawl(source.id, source.name)} className="btn-secondary text-xs flex items-center gap-1 py-1.5">
                    <RefreshCw className="w-3 h-3" /> Обойти
                  </button>
                  <button onClick={() => handleToggle(source.id)} className="btn-secondary text-xs flex items-center gap-1 py-1.5">
                    {source.is_active
                      ? <><ToggleRight className="w-3 h-3 text-green-400" /> Отключить</>
                      : <><ToggleLeft className="w-3 h-3 text-gray-500" /> Включить</>
                    }
                  </button>
                  <button onClick={() => handleDelete(source.id, source.name)} className="btn-danger text-xs flex items-center gap-1 py-1.5 ml-auto">
                    <Trash2 className="w-3 h-3" /> Удалить
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
