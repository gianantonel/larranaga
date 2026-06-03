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
    <div className="min-h-screen flex relative">
      <div className="absolute top-6 right-6 z-10">
        <ThemeToggle />
      </div>

      {/* Columna izquierda: hero (oculta en mobile) */}
      <div className="hidden lg:flex flex-1 items-center justify-center p-16">
        <div className="max-w-md space-y-10">
          <Logo size="xl" />

          <div className="space-y-5">
            <p className="hero-eyebrow">Larrañaga & Asociados</p>
            <h1 className="hero-title text-5xl xl:text-6xl">
              Asesoramiento<br />integral.
            </h1>
            <p className="hero-sub max-w-sm">
              Estudio contable y legal con un equipo de profesionales
              especializados al servicio de tu empresa.
            </p>
          </div>
        </div>
      </div>

      {/* Columna derecha: form */}
      <div
        className="flex-1 flex items-center justify-center p-6 sm:p-12 lg:p-16"
        style={{ background: 'var(--surface)' }}
      >
        <div className="w-full max-w-sm space-y-8">
          <div className="lg:hidden flex justify-center mb-2">
            <Logo size="md" />
          </div>

          <div className="space-y-2">
            <p className="hero-eyebrow">Iniciar sesión</p>
            <h2 className="text-3xl font-bold tracking-apple-2" style={{ color: 'var(--text)' }}>
              Bienvenido
            </h2>
            <p className="text-sm font-light" style={{ color: 'var(--text-subtle)' }}>
              Accedé a la plataforma con tus credenciales.
            </p>
          </div>

          {error && (
            <div className="rounded-2xl px-4 py-3 text-sm chip-danger w-full justify-start">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="label">Correo electrónico</label>
              <div className="relative">
                <Mail size={15} strokeWidth={1.75} className="absolute left-4 top-1/2 -translate-y-1/2"
                  style={{ color: 'var(--text-faint)' }} />
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
                <Lock size={15} strokeWidth={1.75} className="absolute left-4 top-1/2 -translate-y-1/2"
                  style={{ color: 'var(--text-faint)' }} />
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
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-full"
                  style={{ color: 'var(--text-faint)' }}
                  aria-label={showPass ? 'Ocultar' : 'Mostrar'}
                >
                  {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary btn-lg w-full">
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-current/30 border-t-current rounded-full animate-spin" />
                  <span>Ingresando…</span>
                </>
              ) : (
                <>
                  <span>Ingresar</span>
                  <ArrowRight size={15} />
                </>
              )}
            </button>
          </form>

          <div
            className="rounded-2xl px-4 py-3.5 text-xs space-y-1.5"
            style={{ background: 'var(--surface-2)' }}
          >
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em]"
               style={{ color: 'var(--text-faint)' }}>
              Cuentas de prueba
            </p>
            <p style={{ color: 'var(--text-subtle)' }}>
              <span className="font-mono" style={{ color: 'var(--text)' }}>admin1@larranaga.com</span>
              {' · '}admin123
            </p>
            <p style={{ color: 'var(--text-subtle)' }}>
              <span className="font-mono" style={{ color: 'var(--text)' }}>mgonzalez@larranaga.com</span>
              {' · '}colab123
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
