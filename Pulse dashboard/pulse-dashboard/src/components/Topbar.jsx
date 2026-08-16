import { Search, Plus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function Topbar({ onCreateClick, searchValue, onSearchChange }) {
  const navigate = useNavigate()

  return (
    <header className="sticky top-0 z-20 backdrop-blur-md bg-ink/80 border-b border-white/[0.06] px-4 md:px-8 py-4">
      <div className="max-w-3xl mx-auto flex items-center gap-3">
        <div className="relative flex-1">
          <Search size={17} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
          <input
            value={searchValue}
            onChange={(e) => {
              onSearchChange?.(e.target.value)
              navigate('/dashboard/search')
            }}
            placeholder="Search hashtags — #reactjs, #uiux..."
            className="w-full bg-surface-2 border border-white/[0.06] rounded-full py-2.5 pl-10 pr-4 text-sm
                       placeholder:text-muted focus:border-signal/50 focus:ring-1 focus:ring-signal/30 outline-none transition-all"
          />
        </div>
        <button
          onClick={onCreateClick}
          className="flex items-center gap-1.5 bg-signal hover:bg-signal-bright text-white text-sm font-medium
                     px-4 py-2.5 rounded-full transition-all duration-200 shadow-glow active:scale-95"
        >
          <Plus size={16} strokeWidth={2.5} />
          <span className="hidden sm:inline">Post</span>
        </button>
      </div>
    </header>
  )
}
