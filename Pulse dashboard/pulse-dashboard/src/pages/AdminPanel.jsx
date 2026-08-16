import { useOutletContext, Navigate } from 'react-router-dom'
import { ShieldCheck, Users, FileText, TrendingUp } from 'lucide-react'
import PostCard from '../components/PostCard.jsx'
import { useAuth } from '../context/AuthContext.jsx'

export default function AdminPanel() {
  const { user } = useAuth()
  const { posts, toggleLike, addComment, deletePost } = useOutletContext()

  if (user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />
  }

  const stats = [
    { label: 'Total Posts', value: posts.length, icon: FileText, color: 'text-signal-bright' },
    { label: 'Total Likes', value: posts.reduce((s, p) => s + p.likes, 0), icon: TrendingUp, color: 'text-pulse' },
    { label: 'Active Users', value: 128, icon: Users, color: 'text-amber' },
  ]

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <ShieldCheck size={20} className="text-amber" />
        <h1 className="font-display text-2xl font-semibold">Admin Panel</h1>
      </div>
      <p className="text-muted text-sm mb-6">Review and remove posts that violate platform guidelines.</p>

      <div className="grid grid-cols-3 gap-3 mb-8">
        {stats.map((s) => (
          <div key={s.label} className="card-surface rounded-xl p-4 shadow-card">
            <s.icon size={16} className={s.color} />
            <p className="font-display text-xl font-semibold mt-2 font-mono">{s.value}</p>
            <p className="text-xs text-muted mt-0.5">{s.label}</p>
          </div>
        ))}
      </div>

      <h2 className="text-sm font-semibold text-muted uppercase tracking-wide mb-3 font-mono">All Posts</h2>
      <div className="flex flex-col gap-4">
        {posts.map((post, i) => (
          <PostCard
            key={post.id}
            post={post}
            index={i}
            onToggleLike={toggleLike}
            onAddComment={addComment}
            onDelete={deletePost}
            isAdminView
          />
        ))}
        {posts.length === 0 && (
          <p className="text-center text-muted py-12 font-mono text-sm">No posts remaining.</p>
        )}
      </div>
    </div>
  )
}
