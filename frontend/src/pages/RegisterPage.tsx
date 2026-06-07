import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Shield } from 'lucide-react'
import { authApiCalls } from '../api/auth'
import { useAuthStore } from '../store/authStore'

export default function RegisterPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [form, setForm] = useState({
    username: '', email: '', password: '', password2: '', company_name: '', role: 'analyst',
  })
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setErrors({})
    setLoading(true)
    try {
      const { data } = await authApiCalls.register(form)
      setAuth(data.user, data.access, data.refresh)
      navigate('/dashboard')
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: Record<string, string[]> } }
      const responseErrors = axiosError.response?.data || {}
      const formatted: Record<string, string> = {}
      for (const [key, val] of Object.entries(responseErrors)) {
        formatted[key] = Array.isArray(val) ? val[0] : String(val)
      }
      setErrors(formatted)
    } finally {
      setLoading(false)
    }
  }

  const field = (key: keyof typeof form, label: string, type = 'text', placeholder = '') => (
    <div>
      <label className="block text-sm font-medium text-gray-400 mb-1.5">{label}</label>
      <input
        type={type}
        value={form[key]}
        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        className="input"
        placeholder={placeholder}
        required={key !== 'company_name'}
      />
      {errors[key] && <p className="text-red-400 text-xs mt-1">{errors[key]}</p>}
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-blue-600 rounded-2xl mb-4">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">FakeGuard</h1>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8">
          <h2 className="text-lg font-semibold text-white mb-6">Регистрация</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {field('username', 'Логин', 'text', 'username')}
            {field('email', 'Email', 'email', 'email@company.ru')}
            {field('password', 'Пароль', 'password', '••••••••')}
            {field('password2', 'Повтор пароля', 'password', '••••••••')}
            {field('company_name', 'Компания', 'text', 'Название компании')}

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1.5">Роль</label>
              <select
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="input"
              >
                <option value="analyst">Аналитик</option>
                <option value="pr_manager">PR Менеджер</option>
                <option value="admin">Администратор</option>
              </select>
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full py-2.5 mt-2">
              {loading ? 'Регистрация...' : 'Создать аккаунт'}
            </button>
          </form>

          <div className="mt-4 text-center text-sm text-gray-500">
            Уже есть аккаунт?{' '}
            <Link to="/login" className="text-blue-400 hover:text-blue-300">Войти</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
