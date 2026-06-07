import { useEffect, useState } from 'react'
import { Plus, Trash2, ToggleLeft, ToggleRight, Bell } from 'lucide-react'
import { alertsApi } from '../api/alerts'
import type { AlertRule } from '../types'
import { timeAgo } from '../utils'

const CONDITION_LABELS: Record<string, string> = {
  fake_score: 'Fake Score',
  sentiment: 'Тональность',
  toxicity: 'Токсичность',
  keyword: 'Ключевое слово',
  urgency: 'Уровень угрозы',
}

const CHANNEL_LABELS: Record<string, string> = {
  in_app: 'В приложении',
  email: 'Email',
  telegram: 'Telegram',
}

interface RuleForm {
  name: string; condition_type: string; threshold: string; keyword: string;
  urgency_level: string; sentiment_value: string; channel: string;
  telegram_chat_id: string; email_recipients: string;
}

const defaultRuleForm: RuleForm = {
  name: '', condition_type: 'fake_score', threshold: '0.7', keyword: '',
  urgency_level: 'high', sentiment_value: 'negative', channel: 'in_app',
  telegram_chat_id: '', email_recipients: '',
}

export default function AlertsPage() {
  const [rules, setRules] = useState<AlertRule[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<RuleForm>(defaultRuleForm)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const res = await alertsApi.listRules()
      setRules(Array.isArray(res.data) ? res.data : (res.data as { results: AlertRule[] }).results ?? [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload: Record<string, unknown> = {
        name: form.name,
        condition_type: form.condition_type,
        channel: form.channel,
        is_active: true,
      }
      if (['fake_score', 'toxicity'].includes(form.condition_type)) {
        payload.threshold = Number(form.threshold)
      }
      if (form.condition_type === 'keyword') payload.keyword = form.keyword
      if (form.condition_type === 'urgency') payload.urgency_level = form.urgency_level
      if (form.condition_type === 'sentiment') payload.sentiment_value = form.sentiment_value
      if (form.channel === 'telegram') payload.telegram_chat_id = form.telegram_chat_id
      if (form.channel === 'email') payload.email_recipients = form.email_recipients

      await alertsApi.createRule(payload)
      setForm(defaultRuleForm)
      setShowForm(false)
      setMsg('Правило создано!')
      setTimeout(() => setMsg(''), 3000)
      load()
    } catch {
      setMsg('Ошибка при создании правила')
    } finally {
      setSaving(false)
    }
  }

  const handleToggle = async (id: number) => {
    await alertsApi.toggleRule(id)
    load()
  }

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Удалить правило "${name}"?`)) return
    await alertsApi.deleteRule(id)
    load()
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Правила алертов</h1>
          <p className="text-gray-500 mt-1">Настройте условия уведомлений об угрозах</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Новое правило
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
          <div className="text-sm font-medium text-white mb-4">Новое правило алерта</div>
          <form onSubmit={handleSave} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Название *</label>
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" required placeholder="Критический фейк" />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Условие</label>
                <select value={form.condition_type} onChange={(e) => setForm({ ...form, condition_type: e.target.value })} className="input">
                  {Object.entries(CONDITION_LABELS).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
              </div>

              {['fake_score', 'toxicity'].includes(form.condition_type) && (
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Порог (0–1)</label>
                  <input type="number" value={form.threshold} onChange={(e) => setForm({ ...form, threshold: e.target.value })} className="input" min={0} max={1} step={0.05} />
                </div>
              )}
              {form.condition_type === 'keyword' && (
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Ключевое слово</label>
                  <input value={form.keyword} onChange={(e) => setForm({ ...form, keyword: e.target.value })} className="input" placeholder="мошенничество" />
                </div>
              )}
              {form.condition_type === 'urgency' && (
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Минимальный уровень</label>
                  <select value={form.urgency_level} onChange={(e) => setForm({ ...form, urgency_level: e.target.value })} className="input">
                    <option value="medium">Средняя</option>
                    <option value="high">Высокая</option>
                    <option value="critical">Критическая</option>
                  </select>
                </div>
              )}
              {form.condition_type === 'sentiment' && (
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Тональность</label>
                  <select value={form.sentiment_value} onChange={(e) => setForm({ ...form, sentiment_value: e.target.value })} className="input">
                    <option value="negative">Негативная</option>
                    <option value="positive">Позитивная</option>
                    <option value="neutral">Нейтральная</option>
                  </select>
                </div>
              )}

              <div>
                <label className="block text-xs text-gray-500 mb-1">Канал уведомлений</label>
                <select value={form.channel} onChange={(e) => setForm({ ...form, channel: e.target.value })} className="input">
                  {Object.entries(CHANNEL_LABELS).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
              </div>
              {form.channel === 'telegram' && (
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Telegram Chat ID</label>
                  <input value={form.telegram_chat_id} onChange={(e) => setForm({ ...form, telegram_chat_id: e.target.value })} className="input" placeholder="-100123456789" />
                </div>
              )}
              {form.channel === 'email' && (
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-1">Email получатели (через запятую)</label>
                  <input value={form.email_recipients} onChange={(e) => setForm({ ...form, email_recipients: e.target.value })} className="input" placeholder="admin@company.ru, pr@company.ru" />
                </div>
              )}
            </div>

            <div className="flex gap-3 pt-1">
              <button type="submit" disabled={saving} className="btn-primary">{saving ? 'Сохраняю...' : 'Создать'}</button>
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Отмена</button>
            </div>
          </form>
        </div>
      )}

      {/* Rules list */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        </div>
      ) : rules.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Bell className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>Правила алертов ещё не созданы</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {rules.map((rule) => (
            <div key={rule.id} className={`card ${!rule.is_active ? 'opacity-60' : ''}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${rule.is_active ? 'bg-green-400' : 'bg-gray-600'}`} />
                    <span className="font-medium text-white text-sm">{rule.name}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-2 space-y-1">
                    <div>Условие: <span className="text-gray-400">{rule.condition_type_display}</span>
                      {rule.threshold && <span className="text-gray-400"> ≥ {rule.threshold}</span>}
                      {rule.keyword && <span className="text-gray-400"> = «{rule.keyword}»</span>}
                      {rule.urgency_level && rule.condition_type === 'urgency' && <span className="text-gray-400"> ≥ {rule.urgency_level}</span>}
                    </div>
                    <div>Канал: <span className="text-gray-400">{rule.channel_display}</span></div>
                    <div>Срабатываний: <span className="text-gray-400">{rule.notifications_count}</span></div>
                    {rule.last_triggered_at && (
                      <div>Последнее: <span className="text-gray-400">{timeAgo(rule.last_triggered_at)}</span></div>
                    )}
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  <button onClick={() => handleToggle(rule.id)} className="p-1.5 hover:bg-gray-800 rounded transition-colors">
                    {rule.is_active
                      ? <ToggleRight className="w-5 h-5 text-green-400" />
                      : <ToggleLeft className="w-5 h-5 text-gray-500" />
                    }
                  </button>
                  <button onClick={() => handleDelete(rule.id, rule.name)} className="p-1.5 hover:bg-red-900/30 rounded transition-colors">
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
