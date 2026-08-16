import { NavLink } from 'react-router-dom'
import { Home, Search, ShieldCheck, LogOut, Activity } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'

export default function Sidebar() {
  const { user, logout } = useAuth()

  const linkClasses = ({ isActive }) =>
    `flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-medium transition-all duration-200
     ${isActive
        ? 'bg-signal/15 text-signal-bright shadow-[inset_0_0_0_1px_rgba(108,92,231,0.35)]'
        : 'text-muted hover:text-ink-50 hover:bg-white/5'}`

  return (
    <aside className="hidden md:flex flex-col w-64 shrink-0 h-screen sticky top-0 border-r border-white/[0.06] px-4 py-6">
      <div className="flex items-center gap-2 px-2 mb-8">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-signal to-pulse flex items-center justify-center shadow-glow">
          <Activity size={18} className="text-ink" strokeWidth={2.5} />
        </div>
        <span className="font-display font-semibold text-lg tracking-tight">Pulse</span>
      </div>

      <nav className="flex flex-col gap-1">
        <NavLink to="/dashboard" end className={linkClasses}>
          <Home size={18} /> Feed
        </NavLink>
        <NavLink to="/dashboard/search" className={linkClasses}>
          <Search size={18} /> Search
        </NavLink>
        {user?.role === 'admin' && (
          <NavLink to="/dashboard/admin" className={linkClasses}>
            <ShieldCheck size={18} /> Admin
          </NavLink>
        )}
      </nav>

      <div className="mt-auto pt-6 border-t border-white/[0.06]">
        <div className="flex items-center gap-3 px-2 py-2 rounded-xl hover:bg-white/5 transition-colors">
          <img src={user?.avatar} alt="" className="w-9 h-9 rounded-full ring-2 ring-signal/40" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.name}</p>
            <p className="text-xs text-muted font-mono truncate">{user?.role === 'admin' ? 'administrator' : 'member'}</p>
          </div>
          <button
            onClick={logout}
            aria-label="Log out"
            className="text-muted hover:text-amber transition-colors p-1.5 rounded-lg hover:bg-white/5"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  )
}
