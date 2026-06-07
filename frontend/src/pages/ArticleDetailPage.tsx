import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, ExternalLink, RefreshCw, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import { articlesApi } from '../api/articles'
import type { ArticleDetail } from '../types'
import { formatDate, urgencyBadge, urgencyLabel, sentimentBadge, sentimentLabel, fakeScoreBg, scorePercent } from '../utils'

export default function ArticleDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [article, setArticle] = useState<ArticleDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [verifying, setVerifying] = useState(false)

  const load = async () => {
    if (!id) return
    setLoading(true)
    try {
      const res = await articlesApi.get(Number(id))
      setArticle(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [id])

  const handleVerify = async (isReal: boolean) => {
    if (!id) return
    setVerifying(true)
    try {
      await articlesApi.verify(Number(id), isReal)
      await load()
    } finally {
      setVerifying(false)
    }
  }

  const handleReanalyze = async () => {
    if (!id) return
    await articlesApi.reanalyze(Number(id))
    setArticle(prev => prev ? { ...prev, status: 'pending' } : null)
    setTimeout(load, 3000)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  if (!article) return <div className="text-gray-500 text-center py-12">Статья не найдена</div>

  return (
    <div className="max-w-4xl space-y-5">
      {/* Back */}
      <Link to="/articles" className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-300 text-sm">
        <ArrowLeft className="w-4 h-4" /> Назад к ленте
      </Link>

      {/* Title card */}
      <div className="card">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex flex-wrap gap-2 mb-3">
              <span className={`badge border ${urgencyBadge(article.urgency)}`}>{urgencyLabel(article.urgency)}</span>
              <span className={`badge border ${sentimentBadge(article.sentiment)}`}>{sentimentLabel(article.sentiment)}</span>
              {article.topic && <span className="badge bg-gray-800 text-gray-400 border border-gray-700">{article.topic}</span>}
              <span className={`badge border ${article.status === 'processed' ? 'bg-green-900/30 text-green-400 border-green-700/40' : article.status === 'pending' ? 'bg-yellow-900/30 text-yellow-400 border-yellow-700/40' : 'bg-red-900/30 text-red-400 border-red-700/40'}`}>
                {article.status === 'processed' ? 'Обработана' : article.status === 'pending' ? 'Ожидает' : 'Ошибка'}
              </span>
            </div>
            <h1 className="text-xl font-bold text-white">{article.title}</h1>
            <div className="flex flex-wrap items-center gap-3 mt-3 text-sm text-gray-500">
              {article.source && <span>Источник: <span className="text-gray-400">{article.source.name}</span></span>}
              {article.author && <span>Автор: <span className="text-gray-400">{article.author}</span></span>}
              {article.published_at && <span>Опубликовано: {formatDate(article.published_at)}</span>}
              <span>Собрано: {formatDate(article.collected_at)}</span>
            </div>
          </div>
          <a href={article.url} target="_blank" rel="noopener noreferrer" className="btn-secondary flex items-center gap-2 text-sm flex-shrink-0">
            <ExternalLink className="w-4 h-4" /> Открыть
          </a>
        </div>
      </div>

      {/* ML Results */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className={`card text-center ${fakeScoreBg(article.fake_score)}`}>
          <div className="text-3xl font-bold">{scorePercent(article.fake_score)}</div>
          <div className="text-xs mt-1 opacity-70">Fake Score</div>
          <div className="text-xs opacity-50 mt-0.5">Вероятность фейка</div>
        </div>
        <div className="card text-center">
          <div className={`text-lg font-bold ${article.sentiment === 'positive' ? 'text-green-400' : article.sentiment === 'negative' ? 'text-red-400' : 'text-gray-400'}`}>
            {sentimentLabel(article.sentiment)}
          </div>
          <div className="text-xs text-gray-500 mt-1">Тональность</div>
          {article.sentiment_score !== null && (
            <div className="text-xs text-gray-600 mt-0.5">score: {article.sentiment_score?.toFixed(2)}</div>
          )}
        </div>
        <div className="card text-center">
          <div className={`text-3xl font-bold ${(article.toxicity_score ?? 0) > 0.5 ? 'text-red-400' : (article.toxicity_score ?? 0) > 0.3 ? 'text-orange-400' : 'text-green-400'}`}>
            {scorePercent(article.toxicity_score)}
          </div>
          <div className="text-xs text-gray-500 mt-1">Токсичность</div>
        </div>
        <div className="card text-center">
          <div className={`text-lg font-bold ${article.source?.credibility_score ?? 0.7 > 0.7 ? 'text-green-400' : 'text-orange-400'}`}>
            {article.source ? `${Math.round((article.source.credibility_score ?? 0.7) * 100)}%` : '—'}
          </div>
          <div className="text-xs text-gray-500 mt-1">Рейтинг источника</div>
          {article.source && <div className="text-xs text-gray-600 mt-0.5">{article.source.name}</div>}
        </div>
      </div>

      {/* SHAP Explanation */}
      {article.shap_data && (article.shap_data.top_signals?.length > 0 || (article.keywords && article.keywords.length > 0)) && (
        <div className="card">
          <div className="text-sm font-medium text-gray-400 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Объяснение AI (SHAP-анализ)
            {article.shap_data.ai_analyzed && (
              <span className="ml-auto text-xs bg-blue-500/15 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                ✨ Gemini AI
              </span>
            )}
            {article.shap_data.model && !article.shap_data.ai_analyzed && (
              <span className="ml-auto text-xs bg-gray-700/50 text-gray-500 border border-gray-600/30 px-2 py-0.5 rounded-full">
                Keyword-based
              </span>
            )}
          </div>
          {/* Gemini summary */}
          {article.shap_data.summary && (
            <div className="mb-4 p-3 bg-blue-500/5 border border-blue-500/20 rounded-lg">
              <div className="text-xs text-blue-400 mb-1">📝 Краткое содержание (Gemini):</div>
              <div className="text-sm text-gray-300">{article.shap_data.summary}</div>
            </div>
          )}
          {article.shap_data.top_signals?.length > 0 && (
            <div className="mb-4">
              <div className="text-xs text-gray-500 mb-2">Сигналы фейка в тексте:</div>
              <div className="flex flex-wrap gap-2">
                {article.shap_data.top_signals.map((signal) => (
                  <span key={signal} className="px-2 py-1 bg-red-900/30 text-red-300 border border-red-700/40 rounded text-xs font-mono">
                    «{signal}»
                  </span>
                ))}
              </div>
            </div>
          )}
          {article.shap_data.fake_score_components && (
            <div className="mb-4">
              <div className="text-xs text-gray-500 mb-2">Компоненты fake score:</div>
              <div className="space-y-2">
                {Object.entries(article.shap_data.fake_score_components).map(([key, val]) => (
                  <div key={key} className="flex items-center gap-3">
                    <div className="text-xs text-gray-500 w-48">{key.replace(/_/g, ' ')}</div>
                    <div className="flex-1 bg-gray-800 rounded-full h-2">
                      <div
                        className="bg-red-500 h-2 rounded-full"
                        style={{ width: `${Math.min(100, (val as number) * 200)}%` }}
                      />
                    </div>
                    <div className="text-xs text-gray-400 w-10 text-right">{(val as number).toFixed(2)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {article.keywords && article.keywords.length > 0 && (
            <div>
              <div className="text-xs text-gray-500 mb-2">Ключевые слова:</div>
              <div className="flex flex-wrap gap-1.5">
                {article.keywords.slice(0, 15).map((kw) => (
                  <span key={kw} className="px-2 py-0.5 bg-gray-800 text-gray-400 border border-gray-700 rounded text-xs">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Entities */}
      {article.entities && article.entities.length > 0 && (
        <div className="card">
          <div className="text-sm font-medium text-gray-400 mb-3">Найденные сущности (NER)</div>
          <div className="flex flex-wrap gap-2">
            {article.entities.map((ent, i) => (
              <span key={i} className="px-2.5 py-1 bg-blue-900/30 text-blue-300 border border-blue-700/40 rounded-lg text-sm">
                {ent.text}
                <span className="ml-1.5 text-blue-500 text-xs">{ent.label}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Content */}
      {article.content && (
        <div className="card">
          <div className="text-sm font-medium text-gray-400 mb-3">Текст публикации</div>
          <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-line">{article.content}</p>
        </div>
      )}

      {/* Actions */}
      <div className="card">
        <div className="text-sm font-medium text-gray-400 mb-4">Действия</div>
        <div className="flex flex-wrap gap-3">
          {article.is_verified === null && (
            <>
              <button
                onClick={() => handleVerify(false)}
                disabled={verifying}
                className="flex items-center gap-2 px-4 py-2 bg-red-900/40 hover:bg-red-900/60 border border-red-700/50 text-red-300 rounded-lg text-sm font-medium transition-colors"
              >
                <XCircle className="w-4 h-4" /> Подтвердить как фейк
              </button>
              <button
                onClick={() => handleVerify(true)}
                disabled={verifying}
                className="flex items-center gap-2 px-4 py-2 bg-green-900/40 hover:bg-green-900/60 border border-green-700/50 text-green-300 rounded-lg text-sm font-medium transition-colors"
              >
                <CheckCircle className="w-4 h-4" /> Подтвердить как реальное
              </button>
            </>
          )}
          {article.is_verified !== null && (
            <div className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm ${article.is_verified ? 'bg-green-900/30 text-green-300' : 'bg-red-900/30 text-red-300'}`}>
              {article.is_verified ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
              {article.is_verified ? 'Верифицировано как реальное' : 'Верифицировано как фейк'}
            </div>
          )}
          <button
            onClick={handleReanalyze}
            className="flex items-center gap-2 btn-secondary text-sm"
          >
            <RefreshCw className="w-4 h-4" /> Повторный анализ
          </button>
        </div>
      </div>
    </div>
  )
}
