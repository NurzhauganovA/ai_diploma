import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Newspaper, Radio, Bell, AlertTriangle,
  LogOut, Shield, ChevronRight, User,
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { useEffect, useState } from 'react'
import { alertsApi } from '../api/alerts'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Дашборд' },
  { to: '/articles', icon: Newspaper, label: 'Лента угроз' },
  { to: '/sources', icon: Radio, label: 'Источники' },
  { to: '/alerts', icon: AlertTriangle, label: 'Алерты' },
  { to: '/notifications', icon: Bell, label: 'Уведомления' },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    alertsApi.unreadCount().then((r) => setUnreadCount(r.data.count)).catch(() => {})
    const interval = setInterval(() => {
      alertsApi.unreadCount().then((r) => setUnreadCount(r.data.count)).catch(() => {})
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-gray-950">
      {/* Sidebar */}
      <aside className="w-60 bg-gray-900 border-r border-gray-800 flex flex-col">
        {/* Logo */}
        <div className="p-5 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-bold text-white text-sm leading-tight">FakeGuard</div>
              <div className="text-xs text-gray-500">AI Мониторинг</div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group ${
                  isActive
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-600/30'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                }`
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span className="flex-1">{label}</span>
              {to === '/notifications' && unreadCount > 0 && (
                <span className="bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
              <ChevronRight className="w-3 h-3 opacity-0 group-hover:opacity-50 transition-opacity" />
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="p-3 border-t border-gray-800">
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-gray-800/50">
            <div className="w-8 h-8 rounded-full bg-blue-600/30 border border-blue-600/40 flex items-center justify-center flex-shrink-0">
              <User className="w-4 h-4 text-blue-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-gray-200 truncate">{user?.username}</div>
              <div className="text-xs text-gray-500 capitalize">
                {user?.role === 'admin' ? 'Администратор' : user?.role === 'analyst' ? 'Аналитик' : 'PR Менеджер'}
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="text-gray-500 hover:text-red-400 transition-colors p-1"
              title="Выйти"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="min-h-full p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
