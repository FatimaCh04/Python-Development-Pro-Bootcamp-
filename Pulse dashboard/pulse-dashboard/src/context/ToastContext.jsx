/**
 * ToastContext — lightweight global toast system.
 *
 * Variants
 * --------
 * "success"  → signal-violet accent  (post created, comment added, liked)
 * "admin"    → amber accent          (post deleted by admin)
 * "error"    → destructive red-ish   (unexpected failures)
 * "info"     → muted neutral         (generic info)
 *
 * Usage
 *   const { toast } = useToast()
 *   toast('Post created!', 'success')
 *   toast('Post removed.', 'admin')
 */
import { createContext, useContext, useState, useCallback, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, ShieldAlert, Info, XCircle, X } from 'lucide-react'

const ToastContext = createContext(null)

const ICONS = {
  success: <CheckCircle2 size={16} className="text-signal-bright shrink-0" />,
  admin:   <ShieldAlert  size={16} className="text-amber shrink-0" />,
  info:    <Info         size={16} className="text-muted shrink-0" />,
  error:   <XCircle      size={16} className="text-red-400 shrink-0" />,
}

const ACCENT = {
  success: 'border-signal/40 bg-surface-2',
  admin:   'border-amber/40  bg-surface-2',
  info:    'border-white/10  bg-surface-2',
  error:   'border-red-500/30 bg-surface-2',
}

let _idCounter = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const timers = useRef({})

  const dismiss = useCallback((id) => {
    clearTimeout(timers.current[id])
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const toast = useCallback((message, variant = 'success', duration = 3500) => {
    const id = ++_idCounter
    setToasts((prev) => [...prev.slice(-4), { id, message, variant }]) // cap at 5
    timers.current[id] = setTimeout(() => dismiss(id), duration)
  }, [dismiss])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}

      {/* Portal — fixed bottom-right stack */}
      <div
        aria-live="polite"
        aria-atomic="false"
        className="fixed bottom-6 right-4 z-[200] flex flex-col gap-2 items-end
                   pointer-events-none"
      >
        <AnimatePresence initial={false}>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              layout
              initial={{ opacity: 0, y: 16, scale: 0.95 }}
              animate={{ opacity: 1, y: 0,  scale: 1    }}
              exit={{    opacity: 0, y: 8,  scale: 0.97 }}
              transition={{ duration: 0.22, ease: 'easeOut' }}
              className={`pointer-events-auto flex items-center gap-2.5 rounded-xl
                          border px-4 py-3 shadow-card text-sm max-w-xs
                          ${ACCENT[t.variant] ?? ACCENT.info}`}
              role="status"
            >
              {ICONS[t.variant] ?? ICONS.info}
              <span className="flex-1 text-ink-50/90 leading-snug">{t.message}</span>
              <button
                onClick={() => dismiss(t.id)}
                className="ml-1 text-muted hover:text-ink-50 transition-colors rounded-full p-0.5
                           focus-visible:outline focus-visible:outline-2 focus-visible:outline-signal"
                aria-label="Dismiss notification"
              >
                <X size={13} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  )
}

export const useToast = () => {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>')
  return ctx
}
