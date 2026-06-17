import { useAuth } from '../context/AuthContext'
import { useFeatureFlags } from '../context/FeatureFlagsContext'

/**
 * Gate de visibilidad por requisito.
 * - codigo: string ("R-01") o array (cualquiera enabled basta).
 * - isAdmin (super_admin o admin) → siempre ve children.
 * - Resto → solo si flag.enabled === true.
 */
export default function FeatureGate({ codigo, fallback = null, children }) {
  const { isAdmin } = useAuth()
  const { flagsByCodigo, loading } = useFeatureFlags()

  if (isAdmin) return children
  if (loading) return null

  const codes = Array.isArray(codigo) ? codigo : [codigo]
  const isOn = codes.some(c => flagsByCodigo[c]?.enabled)
  return isOn ? children : fallback
}
