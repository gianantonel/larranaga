import { createContext, useContext, useState, useEffect, useRef } from 'react'
import { login as apiLogin, getMe } from '../utils/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const logoutRef = useRef(null)

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  // Keep logoutRef in sync so the event listener always calls latest logout
  logoutRef.current = logout

  useEffect(() => {
    // Listen for 401s dispatched by the axios interceptor
    const handleUnauthorized = () => logoutRef.current()
    window.addEventListener('auth:unauthorized', handleUnauthorized)

    const token = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')

    if (token && storedUser) {
      // Set user from storage immediately so protected routes render right away
      setUser(JSON.parse(storedUser))
      // Validate token against the server in the background
      getMe()
        .then(res => setUser(res.data))
        .catch(err => {
          // Only log out when the server explicitly rejects the token (401)
          // Ignore network errors / server timeouts so a brief hiccup doesn't
          // kick the user out of the app
          if (err.response?.status === 401) {
            logout()
          }
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }

    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const login = async (email, password) => {
    const res = await apiLogin(email, password)
    const { access_token, user: userData } = res.data
    localStorage.setItem('token', access_token)
    localStorage.setItem('user', JSON.stringify(userData))
    setUser(userData)
    return userData
  }

  const isAdmin = user?.role && ['admin1', 'admin2', 'admin3'].includes(user.role)

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, isAdmin }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
