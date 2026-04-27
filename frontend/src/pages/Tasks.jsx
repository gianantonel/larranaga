import { useEffect, useState } from 'react'
import { Plus, Filter, ChevronDown, ChevronRight, MessageSquare, X } from 'lucide-react'
import { getTasks, getClients, getCollaborators, createTask, updateTask, createSubtask, updateSubtask } from '../utils/api'
import { useAuth } from '../context/AuthContext'
import { StatusBadge, TypeBadge } from '../components/UI/Badge'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import { formatDate, formatPeriod, taskTypeConfig, taskStatusConfig } from '../utils/helpers'
import RetencionesPanel from '../components/RetencionesPanel'

const TASK_TYPES = Object.entries(taskTypeConfig).map(([v, c]) => ({ value: v, ...c }))
const TASK_STATUSES = Object.entries(taskStatusConfig).map(([v, c]) => ({ value: v, ...c }))

export default function Tasks() {
  const { user, isAdmin } = useAuth()
  const [tasks, setTasks] = useState([])
  const [clients, setClients] = useState([])
  const [collaborators, setCollaborators] = useState([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState({})
  const [filters, setFilters] = useState({ client_id: '', collaborator_id: '', status: '', type: '' })
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [form, setForm] = useState({ title: '', description: '', task_type: 'ddjj_iva', client_id: '', collaborator_id: '', period: '', due_date: '' })
  const [saving, setSaving] = useState(false)
  const [subtaskInputs, setSubtaskInputs] = useState({})

  const load = () => {
    const params = {}
    if (filters.client_id) params.client_id = filters.client_id
    if (filters.collaborator_id) params.collaborator_id = filters.collaborator_id
    if (filters.status) params.status = filters.status
    if (filters.type) params.type = filters.type

    Promise.all([getTasks(params), getClients(), getCollaborators()])
      .then(([t, c, col]) => { setTasks(t.data); setClients(c.data); setCollaborators(col.data) })
      .catch(err => console.error('Tasks load error:', err))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [filters])

  const handleStatusChange = async (taskId, newStatus, comment) => {
    try {
      const payload = { status: newStatus }
      if (comment) payload.blocker_comment = comment
      await updateTask(taskId, payload)
      load()
    } catch (e) { alert(e.response?.data?.detail || 'Error') }
  }

  const handleSubtaskStatus = async (taskId, subtaskId, newStatus) => {
    try {
      await updateSubtask(taskId, subtaskId, { status: newStatus })
      load()
    } catch (e) {}
  }

  const handleAddSubtask = async (taskId) => {
    const title = subtaskInputs[taskId]?.trim()
    if (!title) return
    try {
      await createSubtask(taskId, { title })
      setSubtaskInputs(prev => ({ ...prev, [taskId]: '' }))
      load()
    } catch (e) {}
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = { ...form }
      if (!payload.collaborator_id) delete payload.collaborator_id
      await createTask(payload)
      setShowCreateModal(false)
      load()
    } catch (e) { alert(e.response?.data?.detail || 'Error') }
    finally { setSaving(false) }
  }

  useEffect(() => {
    if (!showCreateModal) return
    const handleEsc = e => { if (e.key === 'Escape') setShowCreateModal(false) }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [showCreateModal])

  if (loading) return <LoadingSpinner text="Cargando tareas..." />

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="Tareas" subtitle={`${tasks.length} tareas`}>
        <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
          <Plus size={18} /> Nueva tarea
        </button>
      </PageHeader>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select value={filters.client_id} onChange={e => setFilters(f => ({ ...f, client_id: e.target.value }))} className="input-field w-auto">
          <option value="">Todos los clientes</option>
          {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        {isAdmin && (
          <select value={filters.collaborator_id} onChange={e => setFilters(f => ({ ...f, collaborator_id: e.target.value }))} className="input-field w-auto">
            <option value="">Todos los colaboradores</option>
            {collaborators.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        )}
        <select value={filters.status} onChange={e => setFilters(f => ({ ...f, status: e.target.value }))} className="input-field w-auto">
          <option value="">Todos los estados</option>
          {TASK_STATUSES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
        <select value={filters.type} onChange={e => setFilters(f => ({ ...f, type: e.target.value }))} className="input-field w-auto">
          <option value="">Todos los tipos</option>
          {TASK_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
      </div>

      {/* Task list */}
      <div className="space-y-3">
        {tasks.map(task => (
          <div key={task.id} className="card">
            {/* Task header */}
            <div className="flex flex-col sm:flex-row sm:items-start gap-3 justify-between">
              <div className="flex items-start gap-3 flex-1 min-w-0">
                <button
                  onClick={() => setExpanded(e => ({ ...e, [task.id]: !e[task.id] }))}
                  className="mt-0.5 text-gray-500 hover:text-gray-300 transition-colors shrink-0"
                >
                  {expanded[task.id] ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                </button>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start gap-2 flex-wrap">
                    <p className="text-base font-semibold text-white break-words">{task.title}</p>
                    <TypeBadge type={task.task_type} />
                    <StatusBadge status={task.status} />
                  </div>
                  <div className="flex items-center gap-2 sm:gap-4 mt-1.5 text-sm text-gray-500 flex-wrap">
                    <span className="font-medium text-gray-400">{task.client_name}</span>
                    {task.collaborator_name && <span>• {task.collaborator_name}</span>}
                    {task.period && <span>• {formatPeriod(task.period)}</span>}
                    {task.due_date && <span>• Vence: {formatDate(task.due_date)}</span>}
                    {task.subtasks?.length > 0 && (
                      <span>• {task.subtasks.filter(s => s.status === 'terminada').length}/{task.subtasks.length} subtareas</span>
                    )}
                  </div>
                  {task.blocker_comment && (
                    <div className="mt-2 flex items-start gap-2 p-2.5 bg-rose-500/10 rounded-lg border border-rose-500/20">
                      <MessageSquare size={14} className="text-rose-400 mt-0.5 shrink-0" />
                      <p className="text-sm text-rose-300">{task.blocker_comment}</p>
                    </div>
                  )}
                </div>
              </div>
              <select
                value={task.status}
                onChange={e => {
                  const newStatus = e.target.value
                  const comment = newStatus === 'bloqueada' ? prompt('Describir el bloqueo (opcional):') : undefined
                  handleStatusChange(task.id, newStatus, comment)
                }}
                className="text-sm bg-[#1f2937] border border-gray-600/50 text-gray-300 rounded-lg px-2 py-1.5 shrink-0 focus:outline-none w-full sm:w-auto mt-2 sm:mt-0"
              >
                {TASK_STATUSES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
            </div>

            {/* Expanded subtasks */}
            {expanded[task.id] && (
              <div className="mt-4 ml-6 space-y-2 border-t border-gray-700/40 pt-4">
                <p className="text-sm font-semibold text-gray-400 mb-2">Subtareas</p>
                {task.subtasks?.map(sub => (
                  <div key={sub.id} className="flex items-center gap-3">
                    <button
                      onClick={() => handleSubtaskStatus(task.id, sub.id,
                        sub.status === 'terminada' ? 'pendiente' : 'terminada'
                      )}
                      className={`w-5 h-5 rounded-md border-2 flex items-center justify-center shrink-0 transition-all
                        ${sub.status === 'terminada' ? 'bg-emerald-500 border-emerald-500' : 'border-gray-500 hover:border-emerald-400'}`}
                    >
                      {sub.status === 'terminada' && <span className="text-white text-xs">✓</span>}
                    </button>
                    <span className={`text-sm flex-1 ${sub.status === 'terminada' ? 'line-through text-gray-500' : 'text-gray-300'}`}>
                      {sub.title}
                    </span>
                    <StatusBadge status={sub.status} />
                  </div>
                ))}
                {/* Add subtask */}
                <div className="flex gap-2 mt-3">
                  <input
                    value={subtaskInputs[task.id] || ''}
                    onChange={e => setSubtaskInputs(prev => ({ ...prev, [task.id]: e.target.value }))}
                    onKeyDown={e => e.key === 'Enter' && handleAddSubtask(task.id)}
                    placeholder="+ Agregar subtarea..."
                    className="input-field text-sm py-2 flex-1"
                  />
                  <button onClick={() => handleAddSubtask(task.id)} className="btn-secondary text-sm px-3 py-2">Agregar</button>
                </div>

                {task.task_type === 'ddjj_iva' && task.client_id && (
                  <div className="mt-4 pt-4 border-t border-gray-700/40">
                    <p className="text-sm font-semibold text-gray-400 mb-2">Retenciones / Percepciones (ARCA)</p>
                    <RetencionesPanel clientId={task.client_id} defaultPeriod={task.period || ''} />
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {tasks.length === 0 && (
          <div className="text-center py-16 text-gray-500">No hay tareas con los filtros seleccionados.</div>
        )}
      </div>

      {/* Create task modal */}
      {showCreateModal && (
        <div className="modal-backdrop" onClick={() => setShowCreateModal(false)}>
          <div className="modal-panel max-w-lg p-6" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="text-xl font-bold text-white">Nueva tarea</h2>
              <button type="button" onClick={() => setShowCreateModal(false)} className="btn-icon"><X size={18} /></button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div><label className="label">Título *</label><input value={form.title} onChange={e => setForm(f=>({...f, title: e.target.value}))} className="input-field" required /></div>
              <div><label className="label">Descripción</label><textarea value={form.description} onChange={e => setForm(f=>({...f, description: e.target.value}))} className="input-field min-h-[80px] resize-none" /></div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="label">Tipo *</label>
                  <select value={form.task_type} onChange={e => setForm(f=>({...f, task_type: e.target.value}))} className="input-field">
                    {TASK_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="label">Cliente *</label>
                  <select value={form.client_id} onChange={e => setForm(f=>({...f, client_id: e.target.value}))} className="input-field" required>
                    <option value="">Seleccionar...</option>
                    {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="label">Colaborador</label>
                  <select value={form.collaborator_id} onChange={e => setForm(f=>({...f, collaborator_id: e.target.value}))} className="input-field">
                    <option value="">Sin asignar</option>
                    {collaborators.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
                <div><label className="label">Período (YYYY-MM)</label><input value={form.period} onChange={e => setForm(f=>({...f, period: e.target.value}))} placeholder="2024-06" className="input-field font-mono" /></div>
              </div>
              <div><label className="label">Fecha límite</label><input type="date" value={form.due_date} onChange={e => setForm(f=>({...f, due_date: e.target.value}))} className="input-field" /></div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowCreateModal(false)} className="btn-secondary flex-1 justify-center">Cancelar</button>
                <button type="submit" disabled={saving} className="btn-primary flex-1 justify-center">{saving ? 'Guardando...' : 'Crear tarea'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
