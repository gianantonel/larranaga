import { useEffect, useState } from 'react'
import { Plus, UserCheck, Users, X, Upload } from 'lucide-react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { getCollaborators, getCollaboratorStats, createCollaborator } from '../utils/api'
import { useAuth } from '../context/AuthContext'
import { RoleBadge } from '../components/UI/Badge'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import { CHART_COLORS } from '../utils/helpers'
import BulkUploadModal from '../components/UI/BulkUploadModal'

const STATUS_COLORS = { terminada: '#10b981', en_curso: '#0ea5e9', pendiente: '#f59e0b', bloqueada: '#f43f5e' }

export default function Collaborators() {
  const { isAdmin } = useAuth()
  const [collaborators, setCollaborators] = useState([])
  const [stats, setStats] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [showBulkModal, setShowBulkModal] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'collaborator' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const load = () => {
    setError(null)
    Promise.all([getCollaborators(), getCollaboratorStats()])
      .then(([c, s]) => { setCollaborators(c.data); setStats(s.data) })
      .catch(() => setError('No se pudo cargar la información. Verificá que el servidor esté activo.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await createCollaborator(form)
      setShowModal(false)
      setForm({ name: '', email: '', password: '', role: 'collaborator' })
      load()
    } catch (e) { alert(e.response?.data?.detail || 'Error') }
    finally { setSaving(false) }
  }

  useEffect(() => {
    if (!showModal) return
    const handleEsc = e => { if (e.key === 'Escape') setShowModal(false) }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [showModal])

  if (loading) return <LoadingSpinner text="Cargando colaboradores..." />

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="Colaboradores" subtitle={`${collaborators.length} colaboradores activos`}>
        {isAdmin && (
          <div className="flex gap-2">
            <button className="btn-secondary" onClick={() => setShowBulkModal(true)}>
              <Upload size={18} /> Importar
            </button>
            <button className="btn-primary" onClick={() => setShowModal(true)}>
              <Plus size={18} /> Nuevo colaborador
            </button>
          </div>
        )}
      </PageHeader>

      {/* Cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {stats.map(collab => {
          const pieData = [
            { name: 'Terminadas', value: collab.completed,   color: STATUS_COLORS.terminada },
            { name: 'En curso',   value: collab.in_progress, color: STATUS_COLORS.en_curso },
            { name: 'Pendientes', value: collab.pending,     color: STATUS_COLORS.pendiente },
            { name: 'Bloqueadas', value: collab.blocked,     color: STATUS_COLORS.bloqueada },
          ].filter(d => d.value > 0)
          const pct = collab.total_tasks > 0 ? Math.round(collab.completed / collab.total_tasks * 100) : 0
          const col = collaborators.find(c => c.id === collab.collaborator_id)

          return (
            <div key={collab.collaborator_id} className="card hover:border-violet-500/30 transition-all">
              {/* Header */}
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-2xl bg-violet-600/25 border border-violet-500/30 flex items-center justify-center text-lg font-bold text-violet-300">
                  {col?.avatar_initials || collab.collaborator_name.slice(0,2).toUpperCase()}
                </div>
                <div>
                  <p className="text-base font-semibold text-white">{collab.collaborator_name}</p>
                  <p className="text-sm text-gray-400">{col?.email}</p>
                </div>
              </div>

              {/* Stats row */}
              <div className="grid grid-cols-4 gap-2 mb-4">
                {[
                  { label: 'Total', value: collab.total_tasks, color: 'text-white' },
                  { label: 'Hechas', value: collab.completed, color: 'text-emerald-400' },
                  { label: 'Pend.', value: collab.pending, color: 'text-amber-400' },
                  { label: 'Bloq.', value: collab.blocked, color: 'text-rose-400' },
                ].map(s => (
                  <div key={s.label} className="bg-[#0f172a] rounded-lg p-2 text-center border border-gray-700/40">
                    <p className={`text-xl font-bold ${s.color}`}>{s.value}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{s.label}</p>
                  </div>
                ))}
              </div>

              {/* Progress */}
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-1.5">
                  <span className="text-gray-400">Completado</span>
                  <span className={`font-bold ${pct > 70 ? 'text-emerald-400' : pct > 40 ? 'text-amber-400' : 'text-rose-400'}`}>{pct}%</span>
                </div>
                <div className="h-2.5 bg-gray-700 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${pct}%`, background: pct > 70 ? '#10b981' : pct > 40 ? '#f59e0b' : '#f43f5e' }} />
                </div>
              </div>

              {/* Mini pie */}
              {pieData.length > 0 && (
                <div className="flex items-center gap-2">
                  <ResponsiveContainer width={80} height={80}>
                    <PieChart>
                      <Pie data={pieData} dataKey="value" cx="50%" cy="50%" outerRadius={36} innerRadius={18} paddingAngle={2}>
                        {pieData.map((d, i) => <Cell key={i} fill={d.color} />)}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex-1 space-y-1">
                    {pieData.map(d => (
                      <div key={d.name} className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-1.5">
                          <div className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                          <span className="text-gray-400">{d.name}</span>
                        </div>
                        <span className="font-semibold text-gray-300">{d.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="mt-3 pt-3 border-t border-gray-700/40 flex items-center justify-between">
                <span className="text-sm text-gray-500">{collab.clients_count} clientes asignados</span>
                <RoleBadge role={col?.role} />
              </div>
            </div>
          )
        })}
      </div>

      {/* Create modal */}
      {showModal && isAdmin && (
        <div className="modal-backdrop" onClick={() => setShowModal(false)}>
          <div className="modal-panel max-w-md p-6" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="text-xl font-bold text-white">Nuevo colaborador</h2>
              <button type="button" onClick={() => setShowModal(false)} className="btn-icon"><X size={18} /></button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div><label className="label">Nombre completo</label><input value={form.name} onChange={e => setForm(f=>({...f, name: e.target.value}))} className="input-field" required /></div>
              <div><label className="label">Email</label><input type="email" value={form.email} onChange={e => setForm(f=>({...f, email: e.target.value}))} className="input-field" required /></div>
              <div><label className="label">Contraseña</label><input type="password" value={form.password} onChange={e => setForm(f=>({...f, password: e.target.value}))} className="input-field" required /></div>
              <div>
                <label className="label">Rol</label>
                <select value={form.role} onChange={e => setForm(f=>({...f, role: e.target.value}))} className="input-field">
                  <option value="collaborator">Colaborador</option>
                  <option value="admin1">Administrador 1</option>
                  <option value="admin2">Administrador 2</option>
                  <option value="admin3">Administrador 3</option>
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary flex-1 justify-center">Cancelar</button>
                <button type="submit" disabled={saving} className="btn-primary flex-1 justify-center">
                  {saving ? 'Guardando...' : 'Crear'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <BulkUploadModal
        open={showBulkModal}
        onClose={() => { setShowBulkModal(false); load() }}
        entity="collaborators"
      />
    </div>
  )
}
