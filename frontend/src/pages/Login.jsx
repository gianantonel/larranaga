import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Scale, Eye, EyeOff, Lock, Mail } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Credenciales incorrectas')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0f1e] flex items-center justify-center px-4">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-violet-600/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/3 w-64 h-64 bg-sky-600/8 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md relative">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-violet-600 mb-4 shadow-xl shadow-violet-900/50">
            <Scale size={30} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">Larrañaga</h1>
          <p className="text-gray-400 mt-1 text-base">Estudio Contable y Legal</p>
        </div>

        {/* Card */}
        <div className="card border-gray-700/60">
          <h2 className="text-xl font-semibold text-white mb-6">Iniciar sesión</h2>

          {error && (
            <div className="bg-rose-500/15 border border-rose-500/30 rounded-lg px-4 py-3 mb-5 text-rose-400 text-base">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Correo electrónico</label>
              <div className="relative">
                <Mail size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="usuario@larranaga.com"
                  className="input-field pl-11"
                  required
                />
              </div>
            </div>

            <div>
              <label className="label">Contraseña</label>
              <div className="relative">
                <Lock size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="input-field pl-11 pr-12"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPass(p => !p)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center mt-6 py-3 text-lg"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Ingresando...
                </>
              ) : 'Ingresar'}
            </button>
          </form>

          {/* Hint */}
          <div className="mt-6 p-4 bg-[#0f172a] rounded-lg border border-gray-700/40">
            <p className="text-xs text-gray-500 font-medium mb-2">Cuentas de prueba:</p>
            <div className="space-y-1 text-xs text-gray-400">
              <p>admin1@larranaga.com / admin123</p>
              <p>mgonzalez@larranaga.com / colab123</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
