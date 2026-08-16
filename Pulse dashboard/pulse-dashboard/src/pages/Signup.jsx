import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Activity, ArrowRight, Mail, Lock, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import PulseLine from '../components/PulseLine.jsx'

export default function Signup() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    await signup(name, email || 'demo@pulse.app', password)
    setLoading(false)
    navigate('/dashboard')
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      <div className="hidden lg:flex flex-col justify-center px-16 relative overflow-hidden border-r border-white/[0.06]">
        <div className="absolute inset-0 bg-gradient-to-br from-pulse/10 via-transparent to-signal/10" />
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
            Every post, <span className="gradient-text">measured</span>.
          </h1>
          <PulseLine color="#00D9C0" height={50} className="my-6 max-w-md opacity-80" />
          <p className="text-muted max-w-sm leading-relaxed">
            Join the rebuilt platform — clean feeds, transparent moderation, and trends you can
            actually trust.
          </p>
        </motion.div>
      </div>

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

          <h2 className="font-display text-2xl font-semibold mb-1">Create your account</h2>
          <p className="text-muted text-sm mb-7">Start posting in under a minute.</p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="relative">
              <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
              <input
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Full name"
                className="w-full bg-surface-2 border border-white/[0.08] rounded-xl py-3 pl-10 pr-4 text-sm
                           placeholder:text-muted focus:border-signal/50 focus:ring-1 focus:ring-signal/30 outline-none transition-all"
              />
            </div>
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
                placeholder="Create a password"
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
              {loading ? 'Creating account...' : 'Sign up'} <ArrowRight size={16} />
            </button>
          </form>

          <p className="text-center text-sm text-muted mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-signal-bright hover:text-signal font-medium">
              Log in
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  )
}
