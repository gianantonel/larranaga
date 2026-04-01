import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Search, Eye, UserPlus, UserMinus, Pencil, Building2, Phone, Mail } from 'lucide-react'
import { getClients, getCollaborators, assignCollaborator, removeCollaboratorFromClient, createClient } from '../utils/api'
import { useAuth } from '../context/AuthContext'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import { RoleBadge } from '../components/UI/Badge'

export default function Clients() {
  const { isAdmin } = useAuth()
  const navigate = useNavigate()
  const [clients, setClients] = useState([])
  const [collaborators, setCollaborators] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState({ name: '', business_name: '', cuit: '', clave_fiscal: '', address: '', phone: '', email: '', category: '', fiscal_condition: 'Responsable Inscripto', activity_code: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const load = () => {
    setError(null)
    Promise.all([getClients(), getCollaborators()])
      .then(([c, col]) => { setClients(c.data); setCollaborators(col.data) })
      .catch(() => setError('No se pudo cargar la información. Verificá que el servidor esté activo.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const filtered = clients.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.cuit?.includes(search) ||
    c.category?.toLowerCase().includes(search.toLowerCase())
  )

  const handleCreate = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await createClient(form)
      setShowModal(false)
      setForm({ name: '', business_name: '', cuit: '', clave_fiscal: '', address: '', phone: '', email: '', category: '', fiscal_condition: 'Responsable Inscripto', activity_code: '' })
      load()
    } catch (err) {
      alert(err.response?.data?.detail || 'Error al crear cliente')
    } finally { setSaving(false) }
  }

  if (loading) return <LoadingSpinner text="Cargando clientes..." />
  if (error) return <div className="p-6 text-rose-400">{error}</div>

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="Clientes" subtitle={`${clients.length} clientes registrados`}>
        {isAdmin && (
          <button className="btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={18} /> Nuevo cliente
          </button>
        )}
      </PageHeader>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Buscar por nombre, CUIT, categoría..."
          className="input-field pl-11"
        />
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700/60 bg-[#0f172a]/60">
                <th className="table-header">Cliente</th>
                <th className="table-header">CUIT</th>
                <th className="table-header">Categoría</th>
                <th className="table-header">Condición fiscal</th>
                <th className="table-header">Colaboradores</th>
                <th className="table-header text-center">Tareas</th>
                <th className="table-header text-center">Estado</th>
                <th className="table-header text-center">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(client => (
                <tr key={client.id} className="table-row">
                  <td className="table-cell">
                    <div>
                      <p className="font-semibold text-white">{client.name}</p>
                      {client.business_name && <p className="text-sm text-gray-500">{client.business_name}</p>}
                    </div>
                  </td>
                  <td className="table-cell font-mono text-gray-300">{client.cuit || '—'}</td>
                  <td className="table-cell">
                    {client.category
                      ? <span className="badge-blue">{client.category}</span>
                      : <span className="text-gray-600">—</span>}
                  </td>
                  <td className="table-cell text-sm text-gray-300">{client.fiscal_condition || '—'}</td>
                  <td className="table-cell">
                    <div className="flex flex-wrap gap-1">
                      {client.collaborators.length === 0
                        ? <span className="text-gray-600 text-sm">Sin asignar</span>
                        : client.collaborators.map(col => (
                          <span key={col.id} className="badge-purple text-xs">{col.name.split(' ')[0]}</span>
                        ))
                      }
                    </div>
                  </td>
                  <td className="table-cell text-center">
                    <span className="text-white font-semibold">{client.task_count}</span>
                    {client.pending_tasks > 0 && (
                      <span className="ml-1 text-amber-400 text-sm">({client.pending_tasks} pend.)</span>
                    )}
                  </td>
                  <td className="table-cell text-center">
                    <span className={client.is_active ? 'badge-green' : 'badge-gray'}>
                      {client.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="table-cell text-center">
                    <button
                      onClick={() => navigate(`/clientes/${client.id}`)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-600/15 hover:bg-violet-600/30 text-violet-400 text-sm font-medium border border-violet-500/20 transition-colors"
                    >
                      <Eye size={15} /> Ver
                    </button>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={8} className="text-center py-12 text-gray-500">No se encontraron clientes</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
          <div className="bg-[#111827] border border-gray-700 rounded-2xl p-6 w-full max-w-xl shadow-2xl">
            <h2 className="text-xl font-bold text-white mb-5">Nuevo cliente</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div><label className="label">Nombre *</label><input value={form.name} onChange={e => setForm(f=>({...f, name: e.target.value}))} className="input-field" required /></div>
                <div><label className="label">Razón social</label><input value={form.business_name} onChange={e => setForm(f=>({...f, business_name: e.target.value}))} className="input-field" /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><label className="label">CUIT</label><input value={form.cuit} onChange={e => setForm(f=>({...f, cuit: e.target.value}))} placeholder="XX-XXXXXXXX-X" className="input-field font-mono" /></div>
                <div><label className="label">Clave Fiscal</label><input type="password" value={form.clave_fiscal} onChange={e => setForm(f=>({...f, clave_fiscal: e.target.value}))} className="input-field" /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Condición fiscal</label>
                  <select value={form.fiscal_condition} onChange={e => setForm(f=>({...f, fiscal_condition: e.target.value}))} className="input-field">
                    <option>Responsable Inscripto</option>
                    <option>Monotributo</option>
                    <option>Exento</option>
                    <option>No Responsable</option>
                  </select>
                </div>
                <div><label className="label">Categoría</label><input value={form.category} onChange={e => setForm(f=>({...f, category: e.target.value}))} className="input-field" /></div>
              </div>
              <div><label className="label">Dirección</label><input value={form.address} onChange={e => setForm(f=>({...f, address: e.target.value}))} className="input-field" /></div>
              <div className="grid grid-cols-2 gap-4">
                <div><label className="label">Teléfono</label><input value={form.phone} onChange={e => setForm(f=>({...f, phone: e.target.value}))} className="input-field" /></div>
                <div><label className="label">Email</label><input type="email" value={form.email} onChange={e => setForm(f=>({...f, email: e.target.value}))} className="input-field" /></div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary flex-1 justify-center">Cancelar</button>
                <button type="submit" disabled={saving} className="btn-primary flex-1 justify-center">
                  {saving ? 'Guardando...' : 'Crear cliente'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
