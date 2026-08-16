import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

// TODO(backend): Replace mock logic with real calls to your Flask API:
//   POST /api/auth/signup  -> { token, user }
//   POST /api/auth/login   -> { token, user }
// Store the returned JWT and attach it as `Authorization: Bearer <token>`
// on every subsequent request (see src/data/api.js placeholder).

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const saved = localStorage.getItem('pulse_user')
    if (saved) setUser(JSON.parse(saved))
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    // MOCK — swap for fetch('/api/auth/login', { method: 'POST', ... })
    const mockUser = {
      id: 'u1',
      name: email.split('@')[0] || 'demo_user',
      email,
      avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(email)}`,
      role: 'admin', // demo mode — everyone gets admin access
      token: 'mock-jwt-token',
    }
    localStorage.setItem('pulse_user', JSON.stringify(mockUser))
    setUser(mockUser)
    return mockUser
  }

  const signup = async (name, email, password) => {
    // MOCK — swap for fetch('/api/auth/signup', { method: 'POST', ... })
    return login(email, password)
  }

  const logout = () => {
    localStorage.removeItem('pulse_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
