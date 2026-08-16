import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Activity, ArrowRight, Mail, Lock } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import PulseLine from '../components/PulseLine.jsx'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    await login(email || 'demo@pulse.app', password)
    setLoading(false)
    navigate('/dashboard')
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Hero side */}
      <div className="hidden lg:flex flex-col justify-center px-16 relative overflow-hidden border-r border-white/[0.06]">
        <div className="absolute inset-0 bg-gradient-to-br from-signal/10 via-transparent to-pulse/10" />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="relative"
        >
          <div className="flex items-center gap-2 mb-8">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-signal to-pulse flex items-center justify-center shadow-glow">
              <Activity size={20} className="text-ink" strokeWidth={2.5} />
            </div>
            <span className="font-display font-semibold text-xl">Pulse</span>
          </div>
          <h1 className="font-display text-5xl font-semibold leading-[1.1] max-w-md">
            Read the <span className="gradient-text">signal</span>, cut the noise.
          </h1>
          <PulseLine color="#6C5CE7" height={50} className="my-6 max-w-md opacity-80" />
          <p className="text-muted max-w-sm leading-relaxed">
            A rebuilt dashboard for cleaning up legacy platform data — write posts, track what's
            trending, and moderate the feed, all in one clear view.
          </p>
        </motion.div>
      </div>

      {/* Form side */}
      <div className="flex items-center justify-center px-6 py-12">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-sm"
        >
          <div className="lg:hidden flex items-center gap-2 mb-8 justify-center">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-signal to-pulse flex items-center justify-center">
              <Activity size={18} className="text-ink" strokeWidth={2.5} />
            </div>
            <span className="font-display font-semibold text-lg">Pulse</span>
          </div>

          <h2 className="font-display text-2xl font-semibold mb-1">Welcome back</h2>
          <p className="text-muted text-sm mb-7">Log in to check today's pulse.</p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="relative">
              <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-surface-2 border border-white/[0.08] rounded-xl py-3 pl-10 pr-4 text-sm
                           placeholder:text-muted focus:border-signal/50 focus:ring-1 focus:ring-signal/30 outline-none transition-all"
              />
            </div>
            <div className="relative">
              <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                className="w-full bg-surface-2 border border-white/[0.08] rounded-xl py-3 pl-10 pr-4 text-sm
                           placeholder:text-muted focus:border-signal/50 focus:ring-1 focus:ring-signal/30 outline-none transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="mt-2 flex items-center justify-center gap-2 bg-signal hover:bg-signal-bright
                         text-white text-sm font-medium py-3 rounded-xl transition-all shadow-glow active:scale-[0.98] disabled:opacity-60"
            >
              {loading ? 'Signing in...' : 'Log in'} <ArrowRight size={16} />
            </button>
          </form>

          <p className="text-center text-sm text-muted mt-6">
            Don't have an account?{' '}
            <Link to="/signup" className="text-signal-bright hover:text-signal font-medium">
              Sign up
            </Link>
          </p>

        </motion.div>
      </div>
    </div>
  )
}
