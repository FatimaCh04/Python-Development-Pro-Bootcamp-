/**
 * BottomNav — mobile bottom navigation bar (visible on < md).
 *
 * Replaces the sidebar on small screens with a sticky bottom bar.
 * "Create post" button is promoted to the center.
 */
import { NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Home, Search, ShieldCheck, Plus } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'

function BottomNavItem({ to, end, icon: Icon, label }) {
  return (
    <NavLink
      to={to}
      end={end}
      aria-label={label}
      className={({ isActive }) =>
        `relative flex flex-col items-center gap-0.5 flex-1 py-2 text-[10px] font-medium
         transition-colors duration-150 focus-visible:outline focus-visible:outline-2
         focus-visible:outline-signal rounded-lg
         ${isActive ? 'text-signal-bright' : 'text-muted'}`
      }
    >
      {({ isActive }) => (
        <>
          {isActive && (
            <motion.span
              layoutId="bottom-nav-pill"
              className="absolute inset-0 rounded-lg bg-signal/10"
              transition={{ type: 'spring', stiffness: 440, damping: 36 }}
              aria-hidden="true"
            />
          )}
          <Icon size={20} className="relative z-10 shrink-0" aria-hidden="true" />
          <span className="relative z-10 leading-none">{label}</span>
        </>
      )}
    </NavLink>
  )
}

export default function BottomNav({ onCreateClick }) {
  const { user } = useAuth()

  return (
    <nav
      aria-label="Mobile navigation"
      className="md:hidden fixed bottom-0 inset-x-0 z-30 flex items-center
                 bg-surface/95 backdrop-blur-md border-t border-white/[0.07]
                 px-2 pb-[env(safe-area-inset-bottom)]"
    >
      <BottomNavItem to="/dashboard" end icon={Home} label="Feed" />
      <BottomNavItem to="/dashboard/search" icon={Search} label="Search" />

      {/* Centre create button */}
      <div className="flex-1 flex justify-center py-1.5">
        <button
          onClick={onCreateClick}
          aria-label="Create new post"
          className="w-12 h-12 rounded-full bg-signal hover:bg-signal-bright text-white
                     flex items-center justify-center shadow-glow active:scale-95
                     transition-all duration-150
                     focus-visible:outline focus-visible:outline-2 focus-visible:outline-signal
                     focus-visible:outline-offset-2"
        >
          <Plus size={22} strokeWidth={2.5} aria-hidden="true" />
        </button>
      </div>

      {user?.role === 'admin' && (
        <BottomNavItem to="/dashboard/admin" icon={ShieldCheck} label="Admin" />
      )}

      {/* Spacer when no admin link so layout stays balanced */}
      {user?.role !== 'admin' && <div className="flex-1" aria-hidden="true" />}
    </nav>
  )
}
