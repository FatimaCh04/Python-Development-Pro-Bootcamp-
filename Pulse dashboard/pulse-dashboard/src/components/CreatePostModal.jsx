import { useState, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { X, Image as ImageIcon, Hash } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'

export default function CreatePostModal({ open, onClose, onSubmit }) {
  const { user } = useAuth()
  const [content, setContent] = useState('')
  const [imagePreview, setImagePreview] = useState(null)
  const [imageFile, setImageFile] = useState(null)
  const fileRef = useRef(null)

  const extractTags = (text) => Array.from(new Set((text.match(/#[\w]+/g) || []).map((t) => t.toLowerCase())))

  const handleFile = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setImageFile(file)
    setImagePreview(URL.createObjectURL(file))
  }

  const reset = () => {
    setContent('')
    setImagePreview(null)
    setImageFile(null)
  }

  const handleSubmit = () => {
    if (!content.trim()) return
    onSubmit({
      content: content.trim(),
      image: imagePreview, // TODO(backend): upload imageFile to S3, store returned URL instead
      tags: extractTags(content),
    })
    reset()
    onClose()
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center px-4 bg-black/60 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.94, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 8 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg card-surface rounded-2xl p-5 shadow-glow"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display font-semibold text-lg">New Post</h2>
              <button onClick={onClose} className="text-muted hover:text-white p-1.5 rounded-full hover:bg-white/5">
                <X size={18} />
              </button>
            </div>

            <div className="flex items-start gap-3">
              <img src={user?.avatar} alt="" className="w-10 h-10 rounded-full" />
              <textarea
                autoFocus
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="What's happening? Use #hashtags to tag your post..."
                rows={4}
                className="flex-1 bg-transparent resize-none text-sm placeholder:text-muted outline-none leading-relaxed"
              />
            </div>

            {imagePreview && (
              <div className="relative mt-2 rounded-xl overflow-hidden border border-white/[0.08]">
                <img src={imagePreview} alt="" className="w-full max-h-64 object-cover" />
                <button
                  onClick={() => { setImagePreview(null); setImageFile(null) }}
                  className="absolute top-2 right-2 bg-black/60 hover:bg-black/80 text-white rounded-full p-1.5"
                >
                  <X size={14} />
                </button>
              </div>
            )}

            <div className="flex items-center gap-2 mt-1.5 flex-wrap">
              {extractTags(content).map((t) => (
                <span key={t} className="text-xs font-mono text-pulse bg-pulse/10 px-2 py-0.5 rounded-full flex items-center gap-1">
                  <Hash size={10} />{t.slice(1)}
                </span>
              ))}
            </div>

            <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/[0.06]">
              <button
                onClick={() => fileRef.current?.click()}
                className="flex items-center gap-2 text-sm text-signal-bright hover:bg-signal/10 px-3 py-2 rounded-full transition-colors"
              >
                <ImageIcon size={17} /> Add image
              </button>
              <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleFile} />

              <button
                onClick={handleSubmit}
                disabled={!content.trim()}
                className="bg-signal hover:bg-signal-bright disabled:opacity-40 disabled:hover:bg-signal
                           text-white text-sm font-medium px-5 py-2 rounded-full transition-all shadow-glow active:scale-95"
              >
                Post
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
