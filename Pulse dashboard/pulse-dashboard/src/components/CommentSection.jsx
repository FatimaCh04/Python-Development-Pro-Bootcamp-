import { useState } from 'react'
import { CornerDownRight, Send } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'

function Comment({ comment, depth, onReply }) {
  const [replying, setReplying] = useState(false)
  const [text, setText] = useState('')

  const submitReply = () => {
    if (!text.trim()) return
    onReply(comment.id, text.trim())
    setText('')
    setReplying(false)
  }

  return (
    <div className={depth > 0 ? 'ml-6 pl-4 border-l border-white/[0.08]' : ''}>
      <div className="flex gap-2.5 py-2.5 animate-floatUp">
        <img src={comment.author.avatar} alt="" className="w-7 h-7 rounded-full shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="bg-surface-2 rounded-xl px-3 py-2 inline-block max-w-full">
            <p className="text-xs font-medium">{comment.author.name}</p>
            <p className="text-sm text-ink-50/90 break-words">{comment.content}</p>
          </div>
          <div className="flex items-center gap-3 mt-1 ml-1">
            <span className="text-xs text-muted font-mono">{comment.timestamp}</span>
            <button
              onClick={() => setReplying((r) => !r)}
              className="text-xs text-muted hover:text-signal-bright font-medium transition-colors flex items-center gap-1"
            >
              <CornerDownRight size={12} /> Reply
            </button>
          </div>

          {replying && (
            <div className="flex items-center gap-2 mt-2 animate-floatUp">
              <input
                autoFocus
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && submitReply()}
                placeholder="Write a reply..."
                className="flex-1 bg-surface-2 border border-white/[0.08] rounded-full px-3 py-1.5 text-xs
                           placeholder:text-muted focus:border-signal/50 outline-none"
              />
              <button
                onClick={submitReply}
                className="text-signal-bright hover:text-signal p-1.5 rounded-full hover:bg-signal/10 transition-colors"
                aria-label="Send reply"
              >
                <Send size={14} />
              </button>
            </div>
          )}

          {comment.replies?.map((r) => (
            <Comment key={r.id} comment={r} depth={depth + 1} onReply={onReply} />
          ))}
        </div>
      </div>
    </div>
  )
}

export default function CommentSection({ comments, onAddComment }) {
  const { user } = useAuth()
  const [text, setText] = useState('')

  const submit = () => {
    if (!text.trim()) return
    onAddComment(null, text.trim())
    setText('')
  }

  const handleReply = (parentId, content) => {
    onAddComment(parentId, content)
  }

  return (
    <div className="mt-3 pt-3 border-t border-white/[0.06]">
      <div className="flex items-center gap-2.5">
        <img src={user?.avatar} alt="" className="w-7 h-7 rounded-full shrink-0" />
        <div className="flex-1 flex items-center gap-2">
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
            placeholder="Add a comment..."
            className="flex-1 bg-surface-2 border border-white/[0.08] rounded-full px-3.5 py-2 text-sm
                       placeholder:text-muted focus:border-signal/50 focus:ring-1 focus:ring-signal/30 outline-none transition-all"
          />
          <button
            onClick={submit}
            className="text-signal-bright hover:text-white p-2 rounded-full bg-signal/10 hover:bg-signal transition-colors"
            aria-label="Post comment"
          >
            <Send size={14} />
          </button>
        </div>
      </div>

      <div className="mt-1">
        {comments.map((c) => (
          <Comment key={c.id} comment={c} depth={0} onReply={handleReply} />
        ))}
      </div>
    </div>
  )
}
