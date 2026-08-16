import { useState } from 'react'
import { motion } from 'framer-motion'
import { MessageCircle, Trash2, Flag } from 'lucide-react'
import LikeButton from './LikeButton.jsx'
import CommentSection from './CommentSection.jsx'
import { useAuth } from '../context/AuthContext.jsx'

function countComments(comments) {
  return comments.reduce((sum, c) => sum + 1 + countComments(c.replies || []), 0)
}

export default function PostCard({ post, onToggleLike, onAddComment, onDelete, isAdminView, index = 0 }) {
  const { user } = useAuth()
  const [showComments, setShowComments] = useState(false)
  const totalComments = countComments(post.comments)

  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.04 }}
      className="card-surface rounded-2xl p-5 shadow-card hover:shadow-glow/50 transition-shadow duration-300"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <img src={post.author.avatar} alt="" className="w-10 h-10 rounded-full ring-1 ring-white/10" />
          <div>
            <p className="text-sm font-semibold leading-tight">{post.author.name}</p>
            <p className="text-xs text-muted font-mono">{post.author.handle} · {post.timestamp}</p>
          </div>
        </div>

        {isAdminView && (
          <button
            onClick={() => onDelete(post.id)}
            className="flex items-center gap-1.5 text-xs font-medium text-amber hover:text-white
                       bg-amber/10 hover:bg-amber/80 px-3 py-1.5 rounded-full transition-colors"
          >
            <Trash2 size={13} /> Remove
          </button>
        )}
      </div>

      <p className="text-sm leading-relaxed mt-3.5 text-ink-50/95 whitespace-pre-wrap">{post.content}</p>

      {post.image && (
        <div className="mt-3.5 rounded-xl overflow-hidden border border-white/[0.06]">
          <img src={post.image} alt="" className="w-full max-h-[420px] object-cover" loading="lazy" />
        </div>
      )}

      {post.tags?.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-3.5">
          {post.tags.map((tag) => (
            <span key={tag} className="text-xs font-mono text-signal-bright bg-signal/10 px-2.5 py-1 rounded-full">
              {tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center gap-1 mt-4 pt-3 border-t border-white/[0.06]">
        <LikeButton liked={post.liked} count={post.likes} onToggle={() => onToggleLike(post.id)} />
        <button
          onClick={() => setShowComments((s) => !s)}
          className="flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium text-muted
                     hover:text-signal-bright hover:bg-signal/10 transition-colors duration-200"
        >
          <MessageCircle size={17} />
          <span className="font-mono">{totalComments}</span>
        </button>
        <button
          className="flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium text-muted
                     hover:text-amber hover:bg-amber/10 transition-colors duration-200 ml-auto"
          aria-label="Report post"
        >
          <Flag size={15} />
        </button>
      </div>

      {showComments && (
        <CommentSection
          comments={post.comments}
          onAddComment={(parentId, content) => onAddComment(post.id, parentId, content)}
        />
      )}
    </motion.article>
  )
}
