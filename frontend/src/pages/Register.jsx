import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Mail, Lock, UserPlus, CheckCircle, AlertTriangle } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const [form, setForm] = useState({
    name: '',
    last_name: '',
    cuit: '',
    email: '',
    password: '',
    confirmPassword: '',
  })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const validateCUIT = (cuit) => {
    // Remove any non-numeric characters
    const clean = cuit.replace(/[^0-9]/g, '')
    // Must be 11 digits
    if (clean.length !== 11) return false
    // Basic modulus 11 validation for CUIT (Argentina)
    // For simplicity, we'll just check length and that it's all numbers
    // In a real app, you'd implement the full validation
    return /^\d{11}$/.test(clean)
  }

  const validateForm = () => {
    const newErrors = {}
    if (!form.name.trim()) newErrors.name = 'El nombre es requerido'
    if (!form.last_name.trim()) newErrors.last_name = 'El apellido es requerido'
    if (!form.cuit.trim()) newErrors.cuit = 'El CUIT es requerido'
    else if (!validateCUIT(form.cuit)) newErrors.cuit = 'CUIT inválido'
    if (!form.email.trim()) newErrors.email = 'El email es requerido'
    else if (!/\S+@\S+\.\S+/.test(form.email)) newErrors.email = 'Email inválido'
    if (!form.password) newErrors.password = 'La contraseña es requerida'
    else if (form.password.length < 6) newErrors.password = 'La contraseña debe tener al menos 6 caracteres'
    if (form.password !== form.confirmPassword) newErrors.confirmPassword = 'Las contraseñas no coinciden'
    return newErrors
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const formErrors = validateForm()
    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors)
      return
    }
    setErrors({})
    setLoading(true)
    try {
      // Call the register endpoint (we'll need to create this in backend)
      // For now, we'll use the existing invite endpoint which requires admin
      // But we want a public register endpoint. Let's assume we have /auth/register
      // We'll need to create that in backend. For now, we'll simulate or use invite if we are admin?
      // Since we are implementing public registration, we need to create a new endpoint.
      // Let's call /auth/register (we'll create it in backend)
      const res = await fetch('/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: form.name,
          last_name: form.last_name,
          cuit: form.cuit,
          email: form.email,
          password: form.password,
          // role will be set to colaborador by default in backend
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Error de registro')
      setSuccess(true)
      // Optionally, auto-login after registration? 
      // But spec says show message and wait for admin approval.
      // We'll just show success message and maybe redirect to login after a delay.
      setTimeout(() => {
        navigate('/login')
      }, 3000)
    } catch (err) {
      setErrors({ submit: err.message })
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-[#0a0f1e] flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-violet-600 mb-6 shadow-xl">
              <CheckCircle size={30} className="text-green-400" />
            </div>
            <h1 className="text-2xl font-bold text-white">Registro exitoso</h1>
            <p className="text-gray-400 mt-4">
              Tu solicitud ha sido enviada. Un administrador revisará tu perfil pronto.
            </p>
            <p className="text-gray-500 mt-6">
              Serás redirigido a la página de ingreso en 3 segundos...
            </p>
          </div>
        </div>
      </div>
    )
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
            <UserPlus size={30} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">Larrañaga</h1>
          <p className="text-gray-400 mt-1 text-base">Registro de nuevo usuario</p>
        </div>

        {/* Card */}
        <div className="card border-gray-700/60">
          <h2 className="text-xl font-semibold text-white mb-6">Crear cuenta</h2>

          {Object.keys(errors).length > 0 && (
            <div className="bg-rose-500/15 border border-rose-500/30 rounded-lg px-4 py-3 mb-5 text-rose-400 text-base">
              {Object.values(errors)[0]}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Nombre</label>
              <div className="relative">
                <input
                  type="text"
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                  placeholder="Juan"
                  className="input-field pl-3"
                  required
                />
              </div>
            </div>

            <div>
              <label className="label">Apellido</label>
              <div className="relative">
                <input
                  type="text"
                  value={form.last_name}
                  onChange={e => setForm({ ...form, last_name: e.target.value })}
                  placeholder="Pérez"
                  className="input-field pl-3"
                  required
                />
              </div>
            </div>

            <div>
              <label className="label">CUIT</label>
              <div className="relative">
                <input
                  type="text"
                  value={form.cuit}
                  onChange={e => setForm({ ...form, cuit: e.target.value })}
                  placeholder="20-12345678-9"
                  className="input-field pl-3"
                  required
                />
                {errors.cuit && (
                  <p className="text-red-400 text-xs mt-1">{errors.cuit}</p>
                )}
              </div>
            </div>

            <div>
              <label className="label">Correo electrónico</label>
              <div className="relative">
                <Mail size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="email"
                  value={form.email}
                  onChange={e => setForm({ ...form, email: e.target.value })}
                  placeholder="usuario@ejemplo.com"
                  className="input-field pl-11"
                  required
                />
                {errors.email && (
                  <p className="text-red-400 text-xs mt-1">{errors.email}</p>
                )}
              </div>
            </div>

            <div>
              <label className="label">Contraseña</label>
              <div className="relative">
                <Lock size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="password"
                  value={form.password}
                  onChange={e => setForm({ ...form, password: e.target.value })}
                  placeholder="••••••••"
                  className="input-field pl-11 pr-12"
                  required
                />
                {errors.password && (
                  <p className="text-red-400 text-xs mt-1">{errors.password}</p>
                )}
              </div>
            </div>

            <div>
              <label className="label">Confirmar contraseña</label>
              <div className="relative">
                <Lock size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="password"
                  value={form.confirmPassword}
                  onChange={e => setForm({ ...form, confirmPassword: e.target.value })}
                  placeholder="••••••••"
                  className="input-field pl-11 pr-12"
                  required
                />
                {errors.confirmPassword && (
                  <p className="text-red-400 text-xs mt-1">{errors.confirmPassword}</p>
                )}
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
                  Creando cuenta...
                </>
              ) : 'Crear cuenta'}
            </button>
          </form>
        </div>

        {/* Hint */}
        <div className="mt-6 p-4 bg-[#0f172a] rounded-lg border border-gray-700/40">
          <p className="text-xs text-gray-500 font-medium mb-2">¿Ya tenés cuenta?</p>
          <p className="mt-2">
            <a href="/login" className="text-blue-400 hover:text-blue-300 underline">
              Iniciar sesión
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}