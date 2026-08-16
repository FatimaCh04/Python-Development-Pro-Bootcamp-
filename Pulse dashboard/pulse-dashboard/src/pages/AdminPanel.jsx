import { useState, useMemo } from 'react'
import { useOutletContext, Navigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ShieldCheck, Users, FileText, Heart, MessageCircle,
  Trash2, Search, ChevronDown, ChevronUp, Tag,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'

function countComments(comments = []) {
  return comments.reduce((s, c) => s + 1 + countComments(c.replies || []), 0)
}

// ── Stat card ────────────────────────────────────────────────────────────────
function StatCard({ label, value, icon: Icon, colorClass, bgClass }) {
  return (
    <div className="card-surface rounded-2xl p-5 shadow-card flex items-center gap-4">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${bgClass}`}>
        <Icon size={18} className={colorClass} />
      </div>
      <div>
        <p className="font-display text-2xl font-semibold font-mono leading-none">{value}</p>
        <p className="text-xs text-muted mt-1">{label}</p>
      </div>
    </div>
  )
}

// ── Confirm-delete button — asks once before firing ──────────────────────────
function DeleteButton({ postId, onDelete }) {
  const [confirming, setConfirming] = useState(false)

  if (confirming) {
    return (
      <div className="flex items-center gap-1.5">
        <button
          onClick={() => { onDelete(postId); setConfirming(false) }}
          className="text-xs font-semibold text-white bg-red-500/80 hover:bg-red-500 px-2.5 py-1 rounded-full transition-colors"
        >
          Confirm
        </button>
        <button
          onClick={() => setConfirming(false)}
          className="text-xs text-muted hover:text-ink-50 px-2 py-1 rounded-full transition-colors"
        >
          Cancel
        </button>
      </div>
    )
  }

  return (
    <button
      onClick={() => setConfirming(true)}
      className="flex items-center gap-1.5 text-xs font-medium text-amber hover:text-white
                 bg-amber/10 hover:bg-red-500/80 px-3 py-1.5 rounded-full transition-all duration-200"
    >
      <Trash2 size={13} /> Remove
    </button>
  )
}

// ── Main component ───────────────────────────────────────────────────────────
export default function AdminPanel() {
  const { user } = useAuth()
  const { posts, deletePost } = useOutletContext()

  const [search, setSearch]     = useState('')
  const [sortBy, setSortBy]     = useState('newest') // newest | likes | comments
  const [sortDir, setSortDir]   = useState('desc')

  if (user?.role !== 'admin') return <Navigate to="/dashboard" replace />

  // ── Derived stats ──────────────────────────────────────────────────────────
  const totalLikes    = posts.reduce((s, p) => s + p.likes, 0)
  const totalComments = posts.reduce((s, p) => s + countComments(p.comments), 0)
  const uniqueAuthors = new Set(posts.map((p) => p.author.name)).size

  const statCards = [
    { label: 'Total Posts',    value: posts.length, icon: FileText,       colorClass: 'text-signal-bright', bgClass: 'bg-signal/15' },
    { label: 'Total Likes',    value: totalLikes,   icon: Heart,          colorClass: 'text-pulse',         bgClass: 'bg-pulse/15'   },
    { label: 'Total Comments', value: totalComments,icon: MessageCircle,  colorClass: 'text-amber',         bgClass: 'bg-amber/15'   },
    { label: 'Unique Authors', value: uniqueAuthors, icon: Users,         colorClass: 'text-signal-bright', bgClass: 'bg-signal/10'  },
  ]

  // ── Filtering + sorting ────────────────────────────────────────────────────
  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    let list = posts.filter(
      (p) =>
        !q ||
        p.author.name.toLowerCase().includes(q) ||
        p.content.toLowerCase().includes(q) ||
        p.tags?.some((t) => t.toLowerCase().includes(q))
    )

    list = [...list].sort((a, b) => {
      let av, bv
      if (sortBy === 'likes')    { av = a.likes;                        bv = b.likes }
      else if (sortBy === 'comments') { av = countComments(a.comments); bv = countComments(b.comments) }
      else                       { av = a.id;                           bv = b.id }
      return sortDir === 'desc' ? (bv > av ? 1 : -1) : (av > bv ? 1 : -1)
    })

    return list
  }, [posts, search, sortBy, sortDir])

  const toggleSort = (col) => {
    if (sortBy === col) setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'))
    else { setSortBy(col); setSortDir('desc') }
  }

  const SortIcon = ({ col }) => {
    if (sortBy !== col) return <ChevronDown size={13} className="opacity-30" />
    return sortDir === 'desc'
      ? <ChevronDown size={13} className="text-signal-bright" />
      : <ChevronUp   size={13} className="text-signal-bright" />
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-1">
        <ShieldCheck size={20} className="text-amber" />
        <h1 className="font-display text-2xl font-semibold">Admin Panel</h1>
      </div>
      <p className="text-muted text-sm mb-6">
        Platform overview — review posts, track engagement, remove content.
      </p>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        {statCards.map((s) => (
          <StatCard key={s.label} {...s} />
        ))}
      </div>

      {/* Posts section header + search */}
      <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
        <h2 className="text-sm font-semibold text-muted uppercase tracking-wide font-mono">
          All Posts
          <span className="ml-2 text-signal-bright normal-case font-mono">
            ({filtered.length}{filtered.length !== posts.length ? ` of ${posts.length}` : ''})
          </span>
        </h2>

        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter by author, tag, content…"
            className="bg-surface-2 border border-white/[0.08] rounded-xl pl-9 pr-4 py-2 text-sm
                       placeholder:text-muted focus:border-signal/40 focus:ring-1 focus:ring-signal/20 outline-none w-64 transition-all"
          />
        </div>
      </div>

      {/* Table header */}
      <div className="card-surface rounded-2xl shadow-card overflow-hidden">
        {/* Column headers */}
        <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-x-4 px-5 py-3
                        border-b border-white/[0.06] text-xs font-semibold text-muted uppercase tracking-wide font-mono">
          <span>Post</span>
          <button onClick={() => toggleSort('likes')}    className="flex items-center gap-1 hover:text-ink-50 transition-colors">
            <Heart size={12} /> Likes <SortIcon col="likes" />
          </button>
          <button onClick={() => toggleSort('comments')} className="flex items-center gap-1 hover:text-ink-50 transition-colors">
            <MessageCircle size={12} /> Comments <SortIcon col="comments" />
          </button>
          <span className="flex items-center gap-1"><Tag size={12} /> Tags</span>
          <span>Action</span>
        </div>

        {/* Rows */}
        <AnimatePresence initial={false}>
          {filtered.map((post, i) => (
            <motion.div
              key={post.id}
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0, overflow: 'hidden' }}
              transition={{ duration: 0.22 }}
              className={`grid grid-cols-[1fr_auto_auto_auto_auto] gap-x-4 items-center
                          px-5 py-4 border-b border-white/[0.04] last:border-0
                          hover:bg-white/[0.025] transition-colors duration-150`}
            >
              {/* Author + content preview */}
              <div className="flex items-center gap-3 min-w-0">
                <img
                  src={post.author.avatar}
                  alt=""
                  className="w-9 h-9 rounded-full ring-1 ring-white/10 shrink-0"
                />
                <div className="min-w-0">
                  <p className="text-sm font-semibold truncate leading-tight">{post.author.name}</p>
                  <p className="text-xs text-muted truncate mt-0.5 font-mono">{post.author.handle}</p>
                  <p className="text-xs text-ink-50/70 truncate mt-0.5 max-w-xs">{post.content}</p>
                </div>
              </div>

              {/* Likes */}
              <div className="flex items-center gap-1.5 text-sm font-mono text-pulse whitespace-nowrap">
                <Heart size={13} className="shrink-0" />
                {post.likes}
              </div>

              {/* Comments */}
              <div className="flex items-center gap-1.5 text-sm font-mono text-amber whitespace-nowrap">
                <MessageCircle size={13} className="shrink-0" />
                {countComments(post.comments)}
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-1 max-w-[140px]">
                {post.tags?.length > 0
                  ? post.tags.map((tag) => (
                      <span key={tag} className="text-[10px] font-mono text-signal-bright bg-signal/10 px-2 py-0.5 rounded-full whitespace-nowrap">
                        {tag}
                      </span>
                    ))
                  : <span className="text-xs text-muted font-mono">—</span>
                }
              </div>

              {/* Delete */}
              <DeleteButton postId={post.id} onDelete={deletePost} />
            </motion.div>
          ))}
        </AnimatePresence>

        {filtered.length === 0 && (
          <div className="py-16 text-center text-muted font-mono text-sm">
            {search ? `No posts match "${search}"` : 'No posts remaining.'}
          </div>
        )}
      </div>
    </div>
  )
}
