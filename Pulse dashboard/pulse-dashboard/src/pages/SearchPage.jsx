import { useOutletContext } from 'react-router-dom'
import { Search } from 'lucide-react'
import PostCard from '../components/PostCard.jsx'
import { trendingTags } from '../data/mockData.js'

export default function SearchPage() {
  const { posts, toggleLike, addComment, searchQuery, setSearchQuery } = useOutletContext()

  const q = searchQuery.trim().toLowerCase()
  const results = q
    ? posts.filter(
        (p) =>
          p.tags?.some((t) => t.toLowerCase().includes(q.replace('#', ''))) ||
          p.content.toLowerCase().includes(q)
      )
    : posts

  return (
    <div>
      <h1 className="font-display text-2xl font-semibold mb-1">Search</h1>
      <p className="text-muted text-sm mb-5">Find posts by hashtag or keyword.</p>

      <div className="relative mb-5">
        <Search size={17} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
        <input
          autoFocus
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Type a hashtag, e.g. #uiux"
          className="w-full bg-surface-2 border border-white/[0.08] rounded-full py-3 pl-10 pr-4 text-sm
                     placeholder:text-muted focus:border-signal/50 focus:ring-1 focus:ring-signal/30 outline-none transition-all"
        />
      </div>

      {!q && (
        <div className="flex flex-wrap gap-2 mb-6">
          {trendingTags.map((t) => (
            <button
              key={t.tag}
              onClick={() => setSearchQuery(t.tag)}
              className="text-xs font-mono text-signal-bright bg-signal/10 hover:bg-signal/20 px-3 py-1.5 rounded-full transition-colors"
            >
              {t.tag}
            </button>
          ))}
        </div>
      )}

      <div className="flex flex-col gap-4">
        {results.map((post, i) => (
          <PostCard key={post.id} post={post} index={i} onToggleLike={toggleLike} onAddComment={addComment} />
        ))}
        {q && results.length === 0 && (
          <p className="text-center text-muted py-12 font-mono text-sm">No posts found for "{searchQuery}"</p>
        )}
      </div>
    </div>
  )
}
