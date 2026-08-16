import { useOutletContext } from 'react-router-dom'
import { motion } from 'framer-motion'
import PostCard from '../components/PostCard.jsx'
import PulseLine from '../components/PulseLine.jsx'

export default function Feed() {
  const { posts, toggleLike, addComment } = useOutletContext()

  return (
    <div>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-6">
        <h1 className="font-display text-2xl font-semibold">Your Feed</h1>
        <p className="text-muted text-sm mt-1">What's moving across the platform right now.</p>
        <PulseLine color="#6C5CE7" height={28} className="mt-3 opacity-50" />
      </motion.div>

      <div className="flex flex-col gap-4">
        {posts.map((post, i) => (
          <PostCard
            key={post.id}
            post={post}
            index={i}
            onToggleLike={toggleLike}
            onAddComment={addComment}
          />
        ))}
        {posts.length === 0 && (
          <p className="text-center text-muted py-12 font-mono text-sm">No posts yet — be the first to share something.</p>
        )}
      </div>
    </div>
  )
}
