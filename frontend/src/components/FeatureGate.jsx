import { useAuth } from '../context/AuthContext'
import { useFeatureFlags } from '../context/FeatureFlagsContext'

/**
 * Gate de visibilidad por requisito (cascada de 2 niveles).
 * - codigo: string ("R-01") o array (cualquiera visible basta).
 * - super_admin → siempre ve children.
 * - admin       → ve si enabled_admin (lo decide el super_admin).
 * - colaborador → ve si enabled_admin AND enabled (lo decide el admin).
 */
export default function FeatureGate({ codigo, fallback = null, children }) {
  const { user, isSuperAdmin } = useAuth()
  const { flagsByCodigo, loading } = useFeatureFlags()

  if (isSuperAdmin) return children
  if (loading) return null

  const esAdmin = user?.role === 'admin'
  const codes = Array.isArray(codigo) ? codigo : [codigo]
  const isOn = codes.some(c => {
    const f = flagsByCodigo[c]
    if (!f) return false
    return esAdmin ? f.enabled_admin : (f.enabled_admin && f.enabled)
  })
  return isOn ? children : fallback
}
