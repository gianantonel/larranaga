import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Lock, Mail, ArrowRight } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import Logo from '../components/UI/Logo'
import ThemeToggle from '../components/UI/ThemeToggle'

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
    <div className="min-h-screen flex relative overflow-hidden">
      <div className="absolute top-6 right-6 z-10">
        <ThemeToggle />
      </div>

      <div className="absolute inset-0 pointer-events-none">
        <div
          className="absolute top-1/2 left-1/2 w-[800px] h-[800px] -translate-x-1/2 -translate-y-1/2 rounded-full blur-3xl opacity-[0.07]"
          style={{ background: 'radial-gradient(circle, var(--brand) 0%, transparent 70%)' }}
        />
      </div>

      {/* Columna izquierda: brand + slogan (oculta en mobile) */}
      <div className="hidden lg:flex flex-1 items-center justify-center p-12 relative">
        <div className="max-w-md space-y-8 relative z-[1]">
          <Logo size="xl" />
          <div className="space-y-4 pt-6">
            <h1 className="hero-title">
              Asesoramiento<br/>
              <span style={{ color: 'var(--brand)' }}>integral</span>.
            </h1>
            <p className="hero-sub max-w-sm">
              Estudio contable y legal con un equipo de profesionales
              especializados al servicio de tu empresa.
            </p>
          </div>
          <div className="pt-6 flex items-center gap-2 text-sm" style={{ color: 'var(--text-subtle)' }}>
            <span className="w-8 h-px" style={{ background: 'var(--border)' }} />
            <span className="tracking-widest text-[11px] uppercase">Larrañaga & Asociados</span>
          </div>
        </div>
      </div>

      {/* Columna derecha: form */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12 relative z-[1]">
        <div className="w-full max-w-sm space-y-8">
          <div className="lg:hidden flex justify-center mb-4">
            <Logo size="md" />
          </div>

          <div className="space-y-2">
            <h2 className="text-3xl font-bold tracking-tight" style={{ color: 'var(--text)' }}>
              Iniciar sesión
            </h2>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Accedé a la plataforma con tus credenciales.
            </p>
          </div>

          {error && (
            <div className="rounded-2xl px-4 py-3 text-sm"
              style={{ background: 'rgba(220, 38, 38, 0.08)', color: 'var(--brand)' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="label">Correo electrónico</label>
              <div className="relative">
                <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-subtle)' }} />
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="usuario@larranaga.com"
                  className="input pl-11"
                  required
                  autoFocus
                />
              </div>
            </div>

            <div>
              <label className="label">Contraseña</label>
              <div className="relative">
                <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-subtle)' }} />
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="input pl-11 pr-11"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPass(p => !p)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-full hover:bg-black/5 dark:hover:bg-white/5"
                  style={{ color: 'var(--text-subtle)' }}
                  aria-label={showPass ? 'Ocultar' : 'Mostrar'}
                >
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary btn-lg w-full">
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Ingresando…</span>
                </>
              ) : (
                <>
                  <span>Ingresar</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          <div className="rounded-2xl px-4 py-3 text-xs space-y-1"
            style={{ background: 'var(--surface-2)', color: 'var(--text-muted)' }}>
            <p className="font-semibold uppercase tracking-wider text-[10px]" style={{ color: 'var(--text-subtle)' }}>
              Cuentas de prueba
            </p>
            <p><span className="font-mono">admin1@larranaga.com</span> · admin123</p>
            <p><span className="font-mono">mgonzalez@larranaga.com</span> · colab123</p>
          </div>
        </div>
      </div>
    </div>
  )
}
