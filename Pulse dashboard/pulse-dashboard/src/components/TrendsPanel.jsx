import { TrendingUp } from 'lucide-react'
import { trendingTags } from '../data/mockData.js'
import PulseLine from './PulseLine.jsx'

export default function TrendsPanel({ onTagClick }) {
  return (
    <aside className="hidden lg:block w-72 shrink-0 h-screen sticky top-0 px-5 py-6 border-l border-white/[0.06]">
      <div className="card-surface rounded-2xl p-5 shadow-card">
        <div className="flex items-center gap-2 mb-1">
          <TrendingUp size={16} className="text-pulse" />
          <h3 className="font-display font-semibold text-sm tracking-wide">Trending Now</h3>
        </div>
        <PulseLine color="#00D9C0" height={24} className="opacity-60 -ml-1" />
        <ul className="mt-2 flex flex-col">
          {trendingTags.map((t, i) => (
            <li key={t.tag}>
              <button
                onClick={() => onTagClick?.(t.tag)}
                className="w-full text-left py-2.5 group flex items-center justify-between border-b border-white/[0.04] last:border-0"
              >
                <div>
                  <p className="text-xs text-muted font-mono">#{i + 1} · trending</p>
                  <p className="text-sm font-medium group-hover:text-signal-bright transition-colors">{t.tag}</p>
                </div>
                <span className="text-xs text-muted font-mono">{t.posts.toLocaleString()}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="card-surface rounded-2xl p-5 mt-4 shadow-card">
        <h3 className="font-display font-semibold text-sm mb-2">About Pulse</h3>
        <p className="text-xs text-muted leading-relaxed">
          A rebuilt dashboard for a legacy platform's data cleanup — write posts, track trends,
          and moderate the feed in one place.
        </p>
      </div>
    </aside>
  )
}
