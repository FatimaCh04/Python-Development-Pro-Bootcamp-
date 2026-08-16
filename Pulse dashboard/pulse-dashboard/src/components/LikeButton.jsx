import { useState } from 'react'
import { Heart } from 'lucide-react'

export default function LikeButton({ liked, count, onToggle }) {
  const [pop, setPop] = useState(false)

  const handleClick = () => {
    if (!liked) {
      setPop(true)
      setTimeout(() => setPop(false), 600)
    }
    onToggle()
  }

  return (
    <button
      onClick={handleClick}
      className={`group flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium transition-colors duration-200
        ${liked ? 'text-pulse bg-pulse/10' : 'text-muted hover:text-pulse hover:bg-pulse/10'}`}
      aria-pressed={liked}
      aria-label={liked ? 'Unlike post' : 'Like post'}
    >
      <Heart
        size={17}
        className={`${pop ? 'animate-heartbeat' : ''} transition-transform`}
        fill={liked ? '#00D9C0' : 'none'}
        strokeWidth={2}
      />
      <span className="font-mono tabular-nums">{count}</span>
    </button>
  )
}
