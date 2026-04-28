import { useState, useEffect } from 'react'
import api from '../utils/api'
import { useAuth } from '../context/AuthContext'
import { Check, Edit2, X, UserPlus, Loader2 } from 'lucide-react'
import PageHeader from '../components/UI/PageHeader'

const ROLE_LABEL = {
  super_admin: 'Super-Admin',
  admin: 'Admin',
  colaborador: 'Colaborador',
  invitado: 'Invitado',
}

export default function Usuarios() {
  const [activos, setActivos] = useState([])
  const [pendientes, setPendientes] = useState([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(null)   // user being edited
  const [inviting, setInviting] = useState(false)
  const { user: currentUser, assignableRoles } = useAuth()

  useEffect(() => { fetchUsers() }, [])

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const [a, p] = await Promise.all([
        api.get('/users/'),
        api.get('/users/pending'),
      ])
      setActivos(a.data)
      setPendientes(p.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const aprobar = async (id, role) => {
    try {
      await api.patch(`/users/${id}/role`, { role })
      await api.patch(`/users/${id}/approve`)
      fetchUsers()
    } catch (e) {
      alert(e.response?.data?.detail || 'Error al aprobar')
    }
  }

  const guardarRol = async (id, nuevoRol) => {
    try {
      await api.patch(`/users/${id}/role`, { role: nuevoRol })
      setEditing(null)
      fetchUsers()
    } catch (e) {
      alert(e.response?.data?.detail || 'Error al cambiar rol')
    }
  }

  const invitar = async (data) => {
    try {
      await api.post('/users/invite', data)
      setInviting(false)
      fetchUsers()
    } catch (e) {
      alert(e.response?.data?.detail || 'Error al invitar')
    }
  }

  const puedeEditar = (target) => {
    if (target.role === 'super_admin' && currentUser.role !== 'super_admin') return false
    if (target.role === 'admin' && currentUser.role === 'admin' && target.id !== currentUser.id) return false
    return assignableRoles.length > 0
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-start justify-between">
        <PageHeader title="Gestión de Usuarios" subtitle="Administrá los usuarios del estudio" />
        <button
          onClick={() => setInviting(true)}
          className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 text-white px-4 py-2 rounded-lg text-sm font-semibold"
        >
          <UserPlus size={16} /> Invitar usuario
        </button>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-gray-400 text-sm"><Loader2 className="animate-spin" size={16} /> Cargando...</div>
      )}

      {/* PENDIENTES */}
      {pendientes.length > 0 && (
        <div className="card border border-amber-500/30 bg-amber-500/5">
          <h2 className="text-amber-400 font-semibold mb-3">Pendientes de aprobación ({pendientes.length})</h2>
          <table className="w-full text-sm">
            <thead className="text-xs text-gray-400 uppercase">
              <tr className="border-b border-gray-700/50">
                <th className="text-left py-2">Nombre</th>
                <th className="text-left py-2">Apellido</th>
                <th className="text-left py-2">CUIT/CUIL</th>
                <th className="text-left py-2">Email</th>
                <th className="text-left py-2">Asignar rol</th>
                <th className="text-right py-2">Acción</th>
              </tr>
            </thead>
            <tbody>
              {pendientes.map(u => (
                <PendingRow key={u.id} user={u} assignableRoles={assignableRoles} onAprobar={aprobar} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ACTIVOS */}
      <div className="card">
        <h2 className="text-white font-semibold mb-3">Usuarios activos ({activos.length})</h2>
        <table className="w-full text-sm">
          <thead className="text-xs text-gray-400 uppercase">
            <tr className="border-b border-gray-700/50">
              <th className="text-left py-2">Nombre</th>
              <th className="text-left py-2">Apellido</th>
              <th className="text-left py-2">CUIT/CUIL</th>
              <th className="text-left py-2">Email</th>
              <th className="text-left py-2">Rol</th>
              <th className="text-right py-2">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {activos.map(u => (
              <tr key={u.id} className="border-b border-gray-700/30 hover:bg-white/5">
                <td className="py-3 text-gray-200">{u.name}</td>
                <td className="py-3 text-gray-200">{u.last_name || '—'}</td>
                <td className="py-3 text-gray-400">{u.cuit || '—'}</td>
                <td className="py-3 text-gray-400">{u.email}</td>
                <td className="py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    u.role === 'super_admin' ? 'bg-rose-500/20 text-rose-300'
                    : u.role === 'admin' ? 'bg-violet-500/20 text-violet-300'
                    : u.role === 'colaborador' ? 'bg-emerald-500/20 text-emerald-300'
                    : 'bg-gray-500/20 text-gray-300'
                  }`}>{ROLE_LABEL[u.role] || u.role}</span>
                </td>
                <td className="py-3 text-right">
                  {puedeEditar(u) ? (
                    <button
                      onClick={() => setEditing(u)}
                      className="text-gray-400 hover:text-violet-400 transition-colors"
                      title="Editar rol"
                    >
                      <Edit2 size={16} />
                    </button>
                  ) : (
                    <span className="text-gray-700 text-xs">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* MODAL EDIT */}
      {editing && (
        <EditRoleModal
          user={editing}
          assignableRoles={assignableRoles}
          onClose={() => setEditing(null)}
          onSave={guardarRol}
        />
      )}

      {/* MODAL INVITE */}
      {inviting && (
        <InviteModal
          assignableRoles={assignableRoles}
          onClose={() => setInviting(false)}
          onSave={invitar}
        />
      )}
    </div>
  )
}


// ─── Subcomponentes ────────────────────────────────────────────────────────

function PendingRow({ user, assignableRoles, onAprobar }) {
  const [rol, setRol] = useState(assignableRoles[0] || 'colaborador')
  return (
    <tr className="border-b border-gray-700/30">
      <td className="py-3 text-gray-200">{user.name}</td>
      <td className="py-3 text-gray-200">{user.last_name || '—'}</td>
      <td className="py-3 text-gray-400">{user.cuit || '—'}</td>
      <td className="py-3 text-gray-400">{user.email}</td>
      <td className="py-3">
        <select
          value={rol}
          onChange={e => setRol(e.target.value)}
          className="bg-[#0f172a] border border-gray-600 rounded px-2 py-1 text-sm text-white"
        >
          {assignableRoles.map(r => (
            <option key={r} value={r}>{ROLE_LABEL[r]}</option>
          ))}
        </select>
      </td>
      <td className="py-3 text-right">
        <button
          onClick={() => onAprobar(user.id, rol)}
          className="text-emerald-400 hover:text-emerald-300"
          title="Aprobar"
        >
          <Check size={20} />
        </button>
      </td>
    </tr>
  )
}


function EditRoleModal({ user, assignableRoles, onClose, onSave }) {
  const [rol, setRol] = useState(
    assignableRoles.includes(user.role) ? user.role : assignableRoles[0]
  )
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-[#1e293b] rounded-xl p-6 w-96 border border-gray-700" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-semibold">Editar rol de usuario</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X size={18} /></button>
        </div>
        <p className="text-sm text-gray-400 mb-4">
          {user.name} {user.last_name} <span className="text-gray-500">· {user.email}</span>
        </p>
        <label className="text-xs text-gray-400 uppercase">Nuevo rol</label>
        <select
          value={rol}
          onChange={e => setRol(e.target.value)}
          className="w-full bg-[#0f172a] border border-gray-600 rounded px-3 py-2 mt-1 text-white"
        >
          {assignableRoles.map(r => (
            <option key={r} value={r}>{ROLE_LABEL[r]}</option>
          ))}
        </select>
        <div className="flex gap-2 mt-6">
          <button onClick={onClose} className="flex-1 py-2 rounded-lg text-gray-300 hover:bg-white/5 text-sm">Cancelar</button>
          <button
            onClick={() => onSave(user.id, rol)}
            className="flex-1 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-semibold"
          >
            Guardar
          </button>
        </div>
      </div>
    </div>
  )
}


function InviteModal({ assignableRoles, onClose, onSave }) {
  const [form, setForm] = useState({
    name: '', last_name: '', cuit: '', email: '', password: '',
    role: assignableRoles[0] || 'colaborador',
  })
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const valid = form.name && form.email && form.password.length >= 6

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-[#1e293b] rounded-xl p-6 w-[28rem] border border-gray-700" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-semibold">Invitar usuario</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X size={18} /></button>
        </div>
        <p className="text-xs text-gray-500 mb-4">El usuario quedará en estado <span className="text-amber-400">Pendiente</span> hasta que un admin lo apruebe.</p>

        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <Field label="Nombre"   value={form.name}      onChange={v => set('name', v)} />
            <Field label="Apellido" value={form.last_name} onChange={v => set('last_name', v)} />
          </div>
          <Field label="CUIT/CUIL"  value={form.cuit}      onChange={v => set('cuit', v)} />
          <Field label="Email"      value={form.email}     onChange={v => set('email', v)} type="email" />
          <Field label="Contraseña" value={form.password}  onChange={v => set('password', v)} type="password" hint="Mínimo 6 caracteres" />

          <div>
            <label className="text-xs text-gray-400 uppercase">Rol inicial</label>
            <select
              value={form.role}
              onChange={e => set('role', e.target.value)}
              className="w-full bg-[#0f172a] border border-gray-600 rounded px-3 py-2 mt-1 text-white"
            >
              {assignableRoles.map(r => (
                <option key={r} value={r}>{ROLE_LABEL[r]}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex gap-2 mt-6">
          <button onClick={onClose} className="flex-1 py-2 rounded-lg text-gray-300 hover:bg-white/5 text-sm">Cancelar</button>
          <button
            onClick={() => onSave(form)}
            disabled={!valid}
            className="flex-1 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm font-semibold"
          >
            Invitar
          </button>
        </div>
      </div>
    </div>
  )
}


function Field({ label, value, onChange, type = 'text', hint }) {
  return (
    <div>
      <label className="text-xs text-gray-400 uppercase">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full bg-[#0f172a] border border-gray-600 rounded px-3 py-2 mt-1 text-white text-sm"
      />
      {hint && <p className="text-[10px] text-gray-500 mt-0.5">{hint}</p>}
    </div>
  )
}
