import { useState } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar.jsx'
import Topbar from '../components/Topbar.jsx'
import TrendsPanel from '../components/TrendsPanel.jsx'
import CreatePostModal from '../components/CreatePostModal.jsx'
import { initialPosts } from '../data/mockData.js'
import { useAuth } from '../context/AuthContext.jsx'

let idCounter = 100

export default function DashboardLayout() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [posts, setPosts] = useState(initialPosts)
  const [modalOpen, setModalOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const toggleLike = (postId) => {
    setPosts((prev) =>
      prev.map((p) =>
        p.id === postId ? { ...p, liked: !p.liked, likes: p.liked ? p.likes - 1 : p.likes + 1 } : p
      )
    )
    // TODO(backend): PATCH /api/posts/:id/like
  }

  const addComment = (postId, parentId, content) => {
    const newComment = {
      id: `c${idCounter++}`,
      author: { name: user?.name || 'You', avatar: user?.avatar },
      content,
      timestamp: 'now',
      replies: [],
    }

    const insertReply = (comments) =>
      comments.map((c) => {
        if (c.id === parentId) {
          return { ...c, replies: [...(c.replies || []), newComment] }
        }
        if (c.replies?.length) {
          return { ...c, replies: insertReply(c.replies) }
        }
        return c
      })

    setPosts((prev) =>
      prev.map((p) => {
        if (p.id !== postId) return p
        if (parentId === null) {
          return { ...p, comments: [...p.comments, newComment] }
        }
        return { ...p, comments: insertReply(p.comments) }
      })
    )
    // TODO(backend): POST /api/posts/:id/comments  { parentId, content }
  }

  const deletePost = (postId) => {
    setPosts((prev) => prev.filter((p) => p.id !== postId))
    // TODO(backend): DELETE /api/admin/posts/:id
  }

  const createPost = ({ content, image, tags }) => {
    const newPost = {
      id: `p${idCounter++}`,
      author: { name: user?.name || 'You', handle: `@${user?.name || 'you'}`, avatar: user?.avatar },
      content,
      image,
      timestamp: 'now',
      likes: 0,
      liked: false,
      tags,
      comments: [],
    }
    setPosts((prev) => [newPost, ...prev])
    navigate('/dashboard')
    // TODO(backend): POST /api/posts (multipart/form-data if image present -> uploads to S3)
  }

  return (
    <div className="flex">
      <Sidebar />
      <div className="flex-1 min-w-0">
        <Topbar
          onCreateClick={() => setModalOpen(true)}
          searchValue={searchQuery}
          onSearchChange={setSearchQuery}
        />
        <main className="max-w-3xl mx-auto px-4 md:px-8 py-6">
          <Outlet
            context={{
              posts,
              toggleLike,
              addComment,
              deletePost,
              searchQuery,
              setSearchQuery,
            }}
          />
        </main>
      </div>
      <TrendsPanel onTagClick={(tag) => { setSearchQuery(tag); navigate('/dashboard/search') }} />

      <CreatePostModal open={modalOpen} onClose={() => setModalOpen(false)} onSubmit={createPost} />
    </div>
  )
}
