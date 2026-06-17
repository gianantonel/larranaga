import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { getFeatureFlags, updateFeatureFlag } from '../utils/api'
import { useAuth } from './AuthContext'

const FeatureFlagsContext = createContext({
  flags: [],
  flagsByCodigo: {},
  loading: true,
  setFlag: async () => {},
  refresh: async () => {},
  verificationMode: false,
  toggleVerificationMode: () => {},
})

export function FeatureFlagsProvider({ children }) {
  const { user } = useAuth()
  const [flags, setFlags] = useState([])
  const [loading, setLoading] = useState(true)

  const [verificationMode, setVerificationMode] = useState(() => {
    if (typeof window === 'undefined') return false
    return localStorage.getItem('larranaga-verification-mode') === 'true'
  })

  useEffect(() => {
    localStorage.setItem('larranaga-verification-mode', String(verificationMode))
  }, [verificationMode])

  const refresh = useCallback(async () => {
    if (!user) {
      setFlags([])
      setLoading(false)
      return
    }
    setLoading(true)
    try {
      const data = await getFeatureFlags()
      setFlags(data || [])
    } catch {
      setFlags([])
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => { refresh() }, [refresh])

  const setFlag = useCallback(async (codigo, enabled) => {
    const updated = await updateFeatureFlag(codigo, enabled)
    setFlags(prev => prev.map(f => (f.codigo === codigo ? updated : f)))
    return updated
  }, [])

  const toggleVerificationMode = useCallback(() => setVerificationMode(v => !v), [])
  const flagsByCodigo = flags.reduce((acc, f) => { acc[f.codigo] = f; return acc }, {})

  return (
    <FeatureFlagsContext.Provider value={{
      flags, flagsByCodigo, loading, setFlag, refresh,
      verificationMode, toggleVerificationMode,
    }}>
      {children}
    </FeatureFlagsContext.Provider>
  )
}

export const useFeatureFlags = () => useContext(FeatureFlagsContext)
export const useFeatureFlag = (codigo) => {
  const ctx = useContext(FeatureFlagsContext)
  return ctx.flagsByCodigo[codigo] || null
}
