import { useState, useEffect } from 'react'
import api from '../utils/api'
import { DollarSign, Settings, RefreshCw, Package, ChevronDown, ChevronRight, AlertCircle, Check } from 'lucide-react'

const MONTHS = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

function getPeriodo() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

function formatARS(n) {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', minimumFractionDigits: 0 }).format(n || 0)
}

// ─── Modal Configurar Honorario ───────────────────────────────────────────────

function ConfigModal({ client, productos, profesionales, onClose, onSaved }) {
  const [tipo, setTipo] = useState(client.tipo_honorario || 'fijo')
  const [importe, setImporte] = useState(client.importe_honorario || 0)
  const [cantidad, setCantidad] = useState(client.cantidad_unidades || 0)
  const [productoId, setProductoId] = useState(client.producto_ref_id || '')
  const [profesionalId, setProfesionalId] = useState(client.profesional_id || '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleSave() {
    setSaving(true)
    setError('')
    try {
      await api.patch(`/honorarios/clientes/${client.client_id}/config`, {
        tipo_honorario: tipo,
        importe_honorario: tipo === 'fijo' ? Number(importe) : 0,
        cantidad_unidades: tipo === 'producto' ? Number(cantidad) : 0,
        producto_ref_id: tipo === 'producto' && productoId ? Number(productoId) : null,
        profesional_id: profesionalId ? Number(profesionalId) : null,
      })
      onSaved()
      onClose()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  const selectedProd = productos.find(p => p.id === Number(productoId))
  const preview = tipo === 'fijo'
    ? Number(importe)
    : selectedProd ? Number(cantidad) * selectedProd.precio_vigente : 0

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1e293b] rounded-2xl border border-gray-700/50 w-full max-w-md shadow-2xl">
        <div className="px-6 py-4 border-b border-gray-700/40">
          <h3 className="text-lg font-semibold text-white">Configurar Honorario</h3>
          <p className="text-sm text-gray-400 mt-0.5">{client.client_name}</p>
        </div>
        <div className="px-6 py-5 space-y-4">
          {/* Tipo */}
          <div>
            <label className="block text-sm text-gray-300 mb-1.5">Tipo de honorario</label>
            <div className="flex gap-3">
              {['fijo', 'producto'].map(t => (
                <button
                  key={t}
                  onClick={() => setTipo(t)}
                  className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors ${
                    tipo === t
                      ? 'border-violet-500 bg-violet-500/20 text-violet-300'
                      : 'border-gray-600 text-gray-400 hover:border-gray-500'
                  }`}
                >
                  {t === 'fijo' ? 'Importe fijo $' : 'Valor producto'}
                </button>
              ))}
            </div>
          </div>

          {tipo === 'fijo' ? (
            <div>
              <label className="block text-sm text-gray-300 mb-1.5">Importe mensual ($)</label>
              <input
                type="number"
                value={importe}
                onChange={e => setImporte(e.target.value)}
                className="w-full bg-[#0f172a] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-500"
                placeholder="254300"
              />
            </div>
          ) : (
            <>
              <div>
                <label className="block text-sm text-gray-300 mb-1.5">Producto de referencia</label>
                <select
                  value={productoId}
                  onChange={e => setProductoId(e.target.value)}
                  className="w-full bg-[#0f172a] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-500"
                >
                  <option value="">-- Seleccionar --</option>
                  {productos.filter(p => p.activo).map(p => (
                    <option key={p.id} value={p.id}>
                      {p.nombre} — {formatARS(p.precio_vigente)} / {p.unidad}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-300 mb-1.5">Cantidad de unidades</label>
                <input
                  type="number"
                  value={cantidad}
                  onChange={e => setCantidad(e.target.value)}
                  className="w-full bg-[#0f172a] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-500"
                  placeholder="50"
                />
              </div>
            </>
          )}

          {/* Profesional a cargo */}
          <div>
            <label className="block text-sm text-gray-300 mb-1.5">Profesional a cargo</label>
            <select
              value={profesionalId}
              onChange={e => setProfesionalId(e.target.value)}
              className="w-full bg-[#0f172a] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-500"
            >
              <option value="">-- Sin asignar --</option>
              {profesionales.filter(p => p.activo).map(p => (
                <option key={p.id} value={p.id}>
                  {p.nombre} {p.apellido || ''} ({p.tipo})
                </option>
              ))}
            </select>
          </div>

          {/* Preview */}
          {preview > 0 && (
            <div className="bg-violet-500/10 border border-violet-500/30 rounded-lg px-4 py-3">
              <p className="text-xs text-gray-400">Honorario calculado</p>
              <p className="text-xl font-bold text-violet-300">{formatARS(preview)}</p>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 text-red-400 text-sm">
              <AlertCircle size={16} /> {error}
            </div>
          )}
        </div>
        <div className="px-6 py-4 border-t border-gray-700/40 flex gap-3 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors">
            Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {saving ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Modal Gestionar Productos de Referencia ──────────────────────────────────

function ProductosModal({ productos, onClose, onRefresh }) {
  const [form, setForm] = useState({ nombre: '', unidad: 'unidad', precio_vigente: '', fecha_actualizacion: new Date().toISOString().slice(0, 10) })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleAdd() {
    if (!form.nombre || !form.precio_vigente) return
    setSaving(true)
    try {
      await api.post('/honorarios/productos', {
        nombre: form.nombre,
        unidad: form.unidad,
        precio_vigente: Number(form.precio_vigente),
        fecha_actualizacion: form.fecha_actualizacion,
      })
      setForm({ nombre: '', unidad: 'unidad', precio_vigente: '', fecha_actualizacion: new Date().toISOString().slice(0, 10) })
      onRefresh()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error')
    } finally {
      setSaving(false)
    }
  }

  async function handleUpdatePrecio(id, precio) {
    const val = parseFloat(precio)
    if (isNaN(val) || val <= 0) return
    try {
      await api.patch(`/honorarios/productos/${id}`, {
        precio_vigente: val,
        fecha_actualizacion: new Date().toISOString().slice(0, 10),
      })
      onRefresh()
    } catch { /* ignore */ }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1e293b] rounded-2xl border border-gray-700/50 w-full max-w-lg shadow-2xl">
        <div className="px-6 py-4 border-b border-gray-700/40 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Productos de Referencia</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">✕</button>
        </div>
        <div className="px-6 py-4 space-y-4 max-h-[60vh] overflow-y-auto">
          {/* Agregar nuevo */}
          <div className="bg-[#0f172a] rounded-xl p-4 space-y-3">
            <p className="text-sm font-medium text-gray-300">Agregar producto</p>
            <div className="grid grid-cols-2 gap-2">
              <input
                value={form.nombre}
                onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))}
                placeholder="Bolsas de cemento"
                className="col-span-2 bg-[#1e293b] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-500"
              />
              <input
                value={form.unidad}
                onChange={e => setForm(f => ({ ...f, unidad: e.target.value }))}
                placeholder="bolsa / kg / litro"
                className="bg-[#1e293b] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-500"
              />
              <input
                type="number"
                value={form.precio_vigente}
                onChange={e => setForm(f => ({ ...f, precio_vigente: e.target.value }))}
                placeholder="Precio ($)"
                className="bg-[#1e293b] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-500"
              />
            </div>
            {error && <p className="text-red-400 text-xs">{error}</p>}
            <button
              onClick={handleAdd}
              disabled={saving || !form.nombre || !form.precio_vigente}
              className="w-full py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              Agregar
            </button>
          </div>

          {/* Lista de productos */}
          <div className="space-y-2">
            {productos.map(p => (
              <div key={p.id} className="flex items-center gap-3 bg-white/5 rounded-xl px-4 py-3">
                <Package size={16} className="text-violet-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white font-medium">{p.nombre}</p>
                  <p className="text-xs text-gray-400">{p.unidad} — actualizado {p.fecha_actualizacion}</p>
                </div>
                <input
                  type="number"
                  defaultValue={p.precio_vigente}
                  onBlur={e => handleUpdatePrecio(p.id, e.target.value)}
                  className="w-28 bg-[#0f172a] border border-gray-600 rounded-lg px-2 py-1 text-white text-sm text-right focus:outline-none focus:border-violet-500"
                />
              </div>
            ))}
            {productos.length === 0 && (
              <p className="text-gray-500 text-sm text-center py-4">Sin productos registrados</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Página Principal ─────────────────────────────────────────────────────────

export default function Honorarios() {
  const now = new Date()
  const [periodo, setPeriodo] = useState(getPeriodo())
  const [clientes, setClientes] = useState([])
  const [honorariosPeriodo, setHonorariosPeriodo] = useState([])
  const [productos, setProductos] = useState([])
  const [profesionales, setProfesionales] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [configClient, setConfigClient] = useState(null)
  const [showProductos, setShowProductos] = useState(false)
  const [filter, setFilter] = useState('')

  async function fetchAll() {
    setLoading(true)
    try {
      const [resClientes, resProd, resProf, resHon] = await Promise.all([
        api.get('/honorarios/resumen/clientes'),
        api.get('/honorarios/productos'),
        api.get('/profesionales/'),
        api.get(`/honorarios/periodo/${periodo}`),
      ])
      setClientes(resClientes.data)
      setProductos(resProd.data)
      setProfesionales(resProf.data)
      setHonorariosPeriodo(resHon.data)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchAll() }, [periodo])

  async function generateHonorarios() {
    setGenerating(true)
    try {
      await api.post(`/honorarios/calcular/${periodo}`)
      await fetchAll()
    } catch { /* ignore */ }
    finally { setGenerating(false) }
  }

  const honMap = Object.fromEntries(honorariosPeriodo.map(h => [h.client_id, h]))

  const filtrados = clientes.filter(c =>
    !filter || c.client_name.toLowerCase().includes(filter.toLowerCase())
  )
  const conHonorario = filtrados.filter(c => c.importe_calculado > 0)
  const sinHonorario = filtrados.filter(c => c.importe_calculado === 0)

  const totalMes = conHonorario.reduce((s, c) => s + c.importe_calculado, 0)
  const cobrados = honorariosPeriodo.filter(h => h.estado === 'cobrado').reduce((s, h) => s + h.importe, 0)
  const pendientesTotal = totalMes - cobrados

  const [year, month] = periodo.split('-')
  const periodoLabel = `${MONTHS[Number(month) - 1]} ${year}`

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Honorarios</h1>
          <p className="text-gray-400 text-sm mt-0.5">R-03 — Cálculo automático por cliente</p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          <input
            type="month"
            value={periodo}
            onChange={e => setPeriodo(e.target.value)}
            className="bg-[#1e293b] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-500"
          />
          <button
            onClick={() => setShowProductos(true)}
            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-gray-600 rounded-lg text-sm text-gray-300 transition-colors"
          >
            <Package size={16} />
            Productos ref.
          </button>
          <button
            onClick={generateHonorarios}
            disabled={generating}
            className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 rounded-lg text-sm text-white font-medium transition-colors disabled:opacity-50"
          >
            <RefreshCw size={16} className={generating ? 'animate-spin' : ''} />
            {generating ? 'Generando...' : `Generar ${periodoLabel}`}
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total devengado', value: formatARS(totalMes), color: 'text-white' },
          { label: 'Cobrado', value: formatARS(cobrados), color: 'text-green-400' },
          { label: 'Pendiente', value: formatARS(pendientesTotal), color: 'text-yellow-400' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-[#1e293b] rounded-xl border border-gray-700/40 px-5 py-4">
            <p className="text-xs text-gray-400">{label}</p>
            <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
            <p className="text-xs text-gray-500 mt-0.5">{periodoLabel}</p>
          </div>
        ))}
      </div>

      {/* Filtro */}
      <input
        value={filter}
        onChange={e => setFilter(e.target.value)}
        placeholder="Buscar cliente..."
        className="w-full max-w-xs bg-[#1e293b] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-500"
      />

      {loading ? (
        <div className="text-center text-gray-400 py-20">Cargando...</div>
      ) : (
        <div className="space-y-4">
          {/* Tabla clientes con honorario */}
          <div className="bg-[#1e293b] rounded-2xl border border-gray-700/40 overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-700/40">
              <h2 className="text-sm font-semibold text-gray-300">Clientes con honorario configurado ({conHonorario.length})</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-700/40">
                    {['Cliente','Tipo','Config.','Importe mes','Profesional','Estado','Acciones'].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-400 whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {conHonorario.map(c => {
                    const hon = honMap[c.client_id]
                    return (
                      <tr key={c.client_id} className="border-b border-gray-700/20 hover:bg-white/3 transition-colors">
                        <td className="px-4 py-3">
                          <p className="text-white font-medium">{c.client_name}</p>
                          <p className="text-xs text-gray-500">{c.cuit}</p>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                            c.tipo_honorario === 'fijo'
                              ? 'bg-blue-500/20 text-blue-300'
                              : 'bg-amber-500/20 text-amber-300'
                          }`}>
                            {c.tipo_honorario === 'fijo' ? 'Fijo' : 'Producto'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-400 text-xs">
                          {c.tipo_honorario === 'fijo'
                            ? formatARS(c.importe_honorario)
                            : `${c.cantidad_unidades} × ${c.producto_nombre || '?'}`}
                        </td>
                        <td className="px-4 py-3 text-white font-semibold">{formatARS(c.importe_calculado)}</td>
                        <td className="px-4 py-3 text-gray-400 text-xs">{c.profesional_nombre || '—'}</td>
                        <td className="px-4 py-3">
                          {!hon ? (
                            <span className="text-xs text-gray-500">Sin generar</span>
                          ) : hon.estado === 'cobrado' ? (
                            <span className="flex items-center gap-1 text-xs text-green-400">
                              <Check size={12} /> Cobrado
                            </span>
                          ) : (
                            <span className="text-xs text-yellow-400">Pendiente</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => setConfigClient(c)}
                            className="flex items-center gap-1 text-xs text-violet-400 hover:text-violet-300 transition-colors"
                          >
                            <Settings size={13} /> Config.
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                  {conHonorario.length === 0 && (
                    <tr>
                      <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                        Ningún cliente con honorario configurado
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Clientes sin configurar */}
          {sinHonorario.length > 0 && (
            <div className="bg-[#1e293b] rounded-2xl border border-amber-500/20 overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-700/40 flex items-center gap-2">
                <AlertCircle size={15} className="text-amber-400" />
                <h2 className="text-sm font-semibold text-amber-300">Sin honorario configurado ({sinHonorario.length})</h2>
              </div>
              <div className="divide-y divide-gray-700/20">
                {sinHonorario.slice(0, 10).map(c => (
                  <div key={c.client_id} className="px-5 py-3 flex items-center justify-between">
                    <div>
                      <p className="text-sm text-white">{c.client_name}</p>
                      <p className="text-xs text-gray-500">{c.cuit}</p>
                    </div>
                    <button
                      onClick={() => setConfigClient(c)}
                      className="flex items-center gap-1 text-xs text-violet-400 hover:text-violet-300 transition-colors"
                    >
                      <Settings size={13} /> Configurar
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Modales */}
      {configClient && (
        <ConfigModal
          client={configClient}
          productos={productos}
          profesionales={profesionales}
          onClose={() => setConfigClient(null)}
          onSaved={fetchAll}
        />
      )}
      {showProductos && (
        <ProductosModal
          productos={productos}
          onClose={() => setShowProductos(false)}
          onRefresh={fetchAll}
        />
      )}
    </div>
  )
}
