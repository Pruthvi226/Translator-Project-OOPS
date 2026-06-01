import { createContext, useContext, useState, useCallback, useEffect } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token') || null)

  const login = useCallback((newToken) => {
    setToken(newToken)
    localStorage.setItem('token', newToken)
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    localStorage.removeItem('token')
  }, [])

  return (
    <AuthContext.Provider value={{ token, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
