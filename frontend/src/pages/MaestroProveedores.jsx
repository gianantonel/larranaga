import { useEffect, useState, useCallback } from 'react'
import {
  Search, Plus, Pencil, Trash2, CheckCircle2, XCircle,
  RefreshCw, AlertCircle, Database, Globe
} from 'lucide-react'
import {
  getProveedores, createProveedor, updateProveedor, deleteProveedor,
  resolverImputacion
} from '../utils/api'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'

// Badge de fuente (manual / padron / ia)
const FuenteBadge = ({ fuente }) => {
  const map = {
    manual:  { label: 'Manual', cls: 'bg-blue-500/15 text-blue-300 border-blue-500/30' },
    padron:  { label: 'Padrón', cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
    ia:      { label: 'IA',     cls: 'bg-violet-500/15 text-violet-300 border-violet-500/30' },
  }
  const { label, cls } = map[fuente] ?? { label: fuente, cls: 'bg-gray-500/15 text-gray-400 border-gray-600/30' }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {fuente === 'padron' && <Globe size={10} />}
      {fuente === 'ia' && <Database size={10} />}
      {label}
    </span>
  )
}

// Modal alta / edición
function ModalProveedor({ proveedor, onSave, onClose }) {
  const isEditing = !!proveedor?.id
  const [form, setForm] = useState({
    cuit: proveedor?.cuit ?? '',
    razon_social: proveedor?.razon_social ?? '',
    cuenta_contable: proveedor?.cuenta_contable ?? '',
    notas: proveedor?.notas ?? '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError]   = useState(null)

  const handleChange = (e) => setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.cuit.trim()) return setError('El CUIT es obligatorio.')
    setSaving(true)
    setError(null)
    try {
      if (isEditing) {
        await updateProveedor(proveedor.id, {
          razon_social:    form.razon_social || null,
          cuenta_contable: form.cuenta_contable || null,
          notas:           form.notas || null,
        })
      } else {
        await createProveedor({
          cuit:            form.cuit.trim(),
          razon_social:    form.razon_social || null,
          cuenta_contable: form.cuenta_contable || null,
          fuente:          'manual',
          notas:           form.notas || null,
        })
      }
      onSave()
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Error al guardar.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm px-4">
      <div className="bg-[#111827] border border-gray-700/60 rounded-2xl shadow-2xl w-full max-w-md">
        <div className="px-6 pt-6 pb-4 border-b border-gray-700/60 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">
            {isEditing ? 'Editar Proveedor' : 'Nuevo Proveedor'}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 transition-colors">
            <XCircle size={20} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="flex items-center gap-2 text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-lg px-3 py-2">
              <AlertCircle size={14} /> {error}
            </div>
          )}

          <div>
            <label className="label">CUIT *</label>
            <input
              name="cuit"
              value={form.cuit}
              onChange={handleChange}
              disabled={isEditing}
              placeholder="20-12345678-9"
              className="input-field disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="label">Razón Social</label>
            <input
              name="razon_social"
              value={form.razon_social}
              onChange={handleChange}
              placeholder="Empresa S.A."
              className="input-field"
            />
          </div>

          <div>
            <label className="label">Cuenta Contable</label>
            <input
              name="cuenta_contable"
              value={form.cuenta_contable}
              onChange={handleChange}
              placeholder="PIVC · PGAN · 1.1.1.01"
              className="input-field"
            />
            <p className="text-xs text-gray-500 mt-1.5">Código Holistor o código contable propio</p>
          </div>

          <div>
            <label className="label">Notas</label>
            <textarea
              name="notas"
              value={form.notas}
              onChange={handleChange}
              rows={2}
              placeholder="Observaciones opcionales..."
              className="input-field resize-none min-h-[60px]"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancelar
            </button>
            <button type="submit" disabled={saving} className="btn-primary disabled:opacity-50">
              {saving ? 'Guardando…' : isEditing ? 'Guardar cambios' : 'Crear proveedor'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function MaestroProveedores() {
  const [proveedores, setProveedores] = useState([])
  const [loading, setLoading]         = useState(true)
  const [busqueda, setBusqueda]       = useState('')
  const [modal, setModal]             = useState(null)
  const [buscandoCuit, setBuscandoCuit] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(null)
  const [error, setError]             = useState(null)

  const cargar = useCallback(() => {
    setLoading(true)
    setError(null)
    getProveedores(busqueda ? { q: busqueda } : undefined)
      .then(res => setProveedores(res.data))
      .catch(() => setError('No se pudo cargar el maestro de proveedores.'))
      .finally(() => setLoading(false))
  }, [busqueda])

  useEffect(() => { cargar() }, [cargar])

  const handleBuscarEnArca = async (proveedor) => {
    setBuscandoCuit(proveedor.id)
    try {
      const res = await resolverImputacion(proveedor.cuit)
      const data = res.data
      if (data.razon_social && !proveedor.razon_social) {
        await updateProveedor(proveedor.id, { razon_social: data.razon_social, fuente: 'padron' })
        cargar()
      }
      if (data.fuente === 'no_encontrado') {
        alert(`CUIT ${proveedor.cuit} no encontrado en el padrón ARCA.`)
      }
    } catch {
      alert('Error al consultar el padrón ARCA.')
    } finally {
      setBuscandoCuit(null)
    }
  }

  const handleDelete = async (id) => {
    try {
      await deleteProveedor(id)
      setConfirmDelete(null)
      cargar()
    } catch {
      alert('No se pudo eliminar el proveedor.')
    }
  }

  const filtrados = proveedores.filter(p => {
    if (!busqueda) return true
    const q = busqueda.toLowerCase()
    return (
      p.cuit?.toLowerCase().includes(q) ||
      p.razon_social?.toLowerCase().includes(q) ||
      p.cuenta_contable?.toLowerCase().includes(q)
    )
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Maestro de Proveedores"
        subtitle="Caché de imputaciones contables por CUIT — base para el pipeline HWCRARCA"
      />

      {/* Toolbar */}
      <div className="card p-4 flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Buscar por CUIT, razón social o cuenta contable…"
            value={busqueda}
            onChange={e => setBusqueda(e.target.value)}
            className="input-field pl-9"
          />
        </div>
        <button onClick={() => setModal({ proveedor: null })} className="btn-primary shrink-0">
          <Plus size={16} /> Nuevo proveedor
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-3">
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {/* Tabla */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-16"><LoadingSpinner /></div>
        ) : filtrados.length === 0 ? (
          <div className="text-center py-16 text-gray-500">
            <Database size={40} className="mx-auto mb-3 opacity-30" />
            <p className="font-medium text-gray-300">No hay proveedores cargados</p>
            <p className="text-sm mt-1">Creá uno manualmente o procesá un archivo ARCA para autocompletar.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#0f172a]/60 border-b border-gray-700/60">
                <tr>
                  <th className="text-left px-5 py-3 font-medium text-gray-400 uppercase tracking-wide text-xs">CUIT</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-400 uppercase tracking-wide text-xs">Razón Social</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-400 uppercase tracking-wide text-xs">Cuenta Contable</th>
                  <th className="text-center px-5 py-3 font-medium text-gray-400 uppercase tracking-wide text-xs">Fuente</th>
                  <th className="text-center px-5 py-3 font-medium text-gray-400 uppercase tracking-wide text-xs">Activo</th>
                  <th className="text-right px-5 py-3 font-medium text-gray-400 uppercase tracking-wide text-xs">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/50">
                {filtrados.map(p => (
                  <tr key={p.id} className="hover:bg-white/5 transition-colors">
                    <td className="px-5 py-3 font-mono text-gray-300 text-xs">{p.cuit}</td>
                    <td className="px-5 py-3 text-white font-medium">
                      {p.razon_social ?? <span className="text-gray-600 italic">Sin nombre</span>}
                    </td>
                    <td className="px-5 py-3">
                      {p.cuenta_contable ? (
                        <span className="font-mono text-xs bg-white/5 text-gray-200 border border-gray-700/50 px-2 py-0.5 rounded">
                          {p.cuenta_contable}
                        </span>
                      ) : (
                        <span className="text-amber-400 text-xs font-medium">⚠ Sin imputar</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-center">
                      <FuenteBadge fuente={p.fuente} />
                    </td>
                    <td className="px-5 py-3 text-center">
                      {p.activo
                        ? <CheckCircle2 size={16} className="text-emerald-400 mx-auto" />
                        : <XCircle    size={16} className="text-gray-600 mx-auto" />
                      }
                    </td>
                    <td className="px-5 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleBuscarEnArca(p)}
                          disabled={buscandoCuit === p.id}
                          title="Consultar padrón ARCA"
                          className="p-1.5 rounded-lg text-gray-500 hover:text-violet-400 hover:bg-violet-500/10 transition-colors disabled:opacity-40"
                        >
                          <RefreshCw size={14} className={buscandoCuit === p.id ? 'animate-spin' : ''} />
                        </button>
                        <button
                          onClick={() => setModal({ proveedor: p })}
                          title="Editar"
                          className="p-1.5 rounded-lg text-gray-500 hover:text-blue-400 hover:bg-blue-500/10 transition-colors"
                        >
                          <Pencil size={14} />
                        </button>
                        <button
                          onClick={() => setConfirmDelete(p.id)}
                          title="Eliminar"
                          className="p-1.5 rounded-lg text-gray-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Footer con contador */}
        {!loading && filtrados.length > 0 && (
          <div className="px-5 py-3 border-t border-gray-700/50 text-xs text-gray-500">
            {filtrados.length} proveedor{filtrados.length !== 1 ? 'es' : ''} —{' '}
            {filtrados.filter(p => !p.cuenta_contable).length} sin cuenta contable asignada
          </div>
        )}
      </div>

      {/* Modal alta / edición */}
      {modal && (
        <ModalProveedor
          proveedor={modal.proveedor}
          onSave={() => { setModal(null); cargar() }}
          onClose={() => setModal(null)}
        />
      )}

      {/* Confirm delete */}
      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm px-4">
          <div className="bg-[#111827] border border-gray-700/60 rounded-2xl shadow-2xl p-6 max-w-sm w-full">
            <h3 className="text-lg font-semibold text-white mb-2">¿Eliminar proveedor?</h3>
            <p className="text-sm text-gray-400 mb-5">
              Esta acción no se puede deshacer. El CUIT quedará sin imputación contable.
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setConfirmDelete(null)} className="btn-secondary">
                Cancelar
              </button>
              <button onClick={() => handleDelete(confirmDelete)} className="btn-danger">
                Eliminar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
