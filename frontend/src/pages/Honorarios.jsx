import { useEffect, useState } from 'react'
import { Plus, DollarSign, Package, RefreshCw, Settings, TrendingUp, X, Calculator } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import StatCard from '../components/UI/StatCard'
import { formatCurrency, formatDate, formatPeriod } from '../utils/helpers'
import {
  getHonorarios, getClients, getProductosReferencia, getProfesionales,
  calcularHonorario, calcularPeriodo,
  createProducto, updateProducto,
  configurarHonorario,
  getPreviewActualizacion, aplicarActualizacion,
} from '../utils/api'

const todayPeriod = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

export default function Honorarios() {
  const { isAdmin } = useAuth()
  const [honorarios, setHonorarios] = useState([])
  const [clients, setClients] = useState([])
  const [productos, setProductos] = useState([])
  const [profesionales, setProfesionales] = useState([])
  const [period, setPeriod] = useState(todayPeriod())
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  // Producto modal
  const [showProductoModal, setShowProductoModal] = useState(false)
  const [editProducto, setEditProducto] = useState(null)
  const [productoForm, setProductoForm] = useState({ nombre: '', unidad: '', precio_vigente: '' })

  // Config honorario modal
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [configClient, setConfigClient] = useState(null)
  const [configForm, setConfigForm] = useState({
    tipo_honorario: '', importe_honorario: '', producto_ref_id: '', cantidad_unidades: '',
  })

  // Actualización cuatrimestral modal
  const [showActModal, setShowActModal] = useState(false)
  const [actPct, setActPct] = useState('')
  const [actVigente, setActVigente] = useState(todayPeriod())
  const [actPreview, setActPreview] = useState(null)

  const load = () => {
    setLoading(true)
    Promise.all([getHonorarios({ period }), getClients(), getProductosReferencia(), getProfesionales()])
      .then(([h, c, p, pr]) => {
        setHonorarios(h.data)
        setClients(c.data)
        setProductos(p.data)
        setProfesionales(pr.data)
      })
      .catch(err => console.error('Honorarios load error:', err))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [period])

  // ─── Calcular ────────────────────────────────────────────────────────────────

  const handleCalcularOne = async (clientId) => {
    setBusy(true)
    try {
      await calcularHonorario(clientId, period)
      load()
    } catch (e) {
      alert(e.response?.data?.detail || 'Error al calcular honorario')
    } finally { setBusy(false) }
  }

  const handleCalcularPeriodo = async () => {
    if (!confirm(`¿Calcular honorarios para todos los clientes configurados en ${formatPeriod(period)}?`)) return
    setBusy(true)
    try {
      const res = await calcularPeriodo(period)
      alert(`Honorarios calculados: ${res.data.length}`)
      load()
    } catch (e) {
      alert(e.response?.data?.detail || 'Error al calcular período')
    } finally { setBusy(false) }
  }

  // ─── Productos ───────────────────────────────────────────────────────────────

  const openProductoModal = (prod = null) => {
    setEditProducto(prod)
    setProductoForm(prod
      ? { nombre: prod.nombre, unidad: prod.unidad || '', precio_vigente: prod.precio_vigente }
      : { nombre: '', unidad: '', precio_vigente: '' }
    )
    setShowProductoModal(true)
  }

  const handleSaveProducto = async (e) => {
    e.preventDefault()
    const data = {
      nombre: productoForm.nombre,
      unidad: productoForm.unidad || null,
      precio_vigente: parseFloat(productoForm.precio_vigente),
    }
    try {
      if (editProducto) await updateProducto(editProducto.id, data)
      else await createProducto(data)
      setShowProductoModal(false)
      load()
    } catch (e) { alert(e.response?.data?.detail || 'Error al guardar producto') }
  }

  // ─── Configurar cliente ──────────────────────────────────────────────────────

  const openConfigModal = (client) => {
    setConfigClient(client)
    setConfigForm({
      tipo_honorario: client.tipo_honorario || '',
      importe_honorario: client.importe_honorario ?? '',
      producto_ref_id: client.producto_ref_id ?? '',
      cantidad_unidades: client.cantidad_unidades ?? '',
      profesional_id: client.profesional_id ?? '',
    })
    setShowConfigModal(true)
  }

  const handleSaveConfig = async (e) => {
    e.preventDefault()
    const data = {
      tipo_honorario: configForm.tipo_honorario || null,
      importe_honorario: configForm.importe_honorario !== '' ? parseFloat(configForm.importe_honorario) : null,
      producto_ref_id: configForm.producto_ref_id !== '' ? parseInt(configForm.producto_ref_id) : null,
      cantidad_unidades: configForm.cantidad_unidades !== '' ? parseFloat(configForm.cantidad_unidades) : null,
      profesional_id: configForm.profesional_id !== '' ? parseInt(configForm.profesional_id) : null,
    }
    try {
      await configurarHonorario(configClient.id, data)
      setShowConfigModal(false)
      load()
    } catch (e) { alert(e.response?.data?.detail || 'Error al configurar cliente') }
  }

  // ─── Actualización cuatrimestral ─────────────────────────────────────────────

  const handlePreviewAct = async () => {
    const pct = parseFloat(actPct)
    if (isNaN(pct) || pct <= 0) { alert('Ingresá un porcentaje válido mayor a 0'); return }
    try {
      const res = await getPreviewActualizacion(pct)
      setActPreview(res.data)
    } catch (e) { alert(e.response?.data?.detail || 'Error al generar vista previa') }
  }

  const handleAplicarAct = async () => {
    if (!actPreview) return
    if (!confirm(`¿Aplicar actualización de ${actPreview.indice_pct}% vigente desde ${formatPeriod(actVigente)}? Esta acción modifica los importes de los clientes.`)) return
    const data = {
      indice_pct: actPreview.indice_pct,
      vigente_desde: actVigente,
      actualizaciones: actPreview.clientes
        .filter(c => c.aplica_indice)
        .map(c => ({ client_id: c.client_id, nuevo_importe: c.importe_propuesto, confirmar: true })),
    }
    try {
      const res = await aplicarActualizacion(data)
      alert(`Actualización aplicada: ${res.data.actualizados} clientes actualizados`)
      setShowActModal(false)
      setActPreview(null)
      setActPct('')
      load()
    } catch (e) { alert(e.response?.data?.detail || 'Error al aplicar actualización') }
  }

  if (loading) return <LoadingSpinner text="Cargando honorarios..." />

  const totalImporte = honorarios.reduce((a, h) => a + h.importe, 0)
  const sinConfig = clients.filter(c => c.is_active && !c.tipo_honorario).length

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="Honorarios" subtitle="Cálculo mensual de honorarios por cliente">
        <div className="flex flex-wrap gap-2 items-center">
          <input
            type="month"
            value={period}
            onChange={e => setPeriod(e.target.value)}
            className="input-field w-auto"
          />
          {isAdmin && (
            <>
              <button onClick={handleCalcularPeriodo} disabled={busy} className="btn-primary">
                <RefreshCw size={16} /> Calcular período
              </button>
              <button onClick={() => setShowActModal(true)} className="btn-secondary">
                <TrendingUp size={16} /> Actualización cuatrimestral
              </button>
            </>
          )}
        </div>
      </PageHeader>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <StatCard title="Honorarios calculados" value={honorarios.length} icon={Calculator} color="violet" />
        <StatCard title={`Total ${formatPeriod(period)}`} value={formatCurrency(totalImporte)} icon={DollarSign} color="emerald" />
        <StatCard title="Productos referencia" value={productos.length} icon={Package} color="amber" />
      </div>

      {/* Alerta clientes sin config */}
      {isAdmin && sinConfig > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl px-4 py-3 text-sm text-amber-300">
          {sinConfig} cliente{sinConfig > 1 ? 's' : ''} activo{sinConfig > 1 ? 's' : ''} sin honorario configurado. Usá el botón <Settings size={12} className="inline" /> en la tabla para configurarlos.
        </div>
      )}

      {/* Productos de referencia */}
      {isAdmin && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-white">Productos de referencia</h3>
            <button className="btn-primary text-sm py-1.5" onClick={() => openProductoModal()}>
              <Plus size={15} /> Nuevo producto
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700/60 bg-[#0f172a]/60">
                  <th className="table-header">Nombre</th>
                  <th className="table-header">Unidad</th>
                  <th className="table-header text-right">Precio vigente</th>
                  <th className="table-header">Actualizado</th>
                  <th className="table-header"></th>
                </tr>
              </thead>
              <tbody>
                {productos.map(p => (
                  <tr key={p.id} className="table-row">
                    <td className="table-cell font-medium text-white">{p.nombre}</td>
                    <td className="table-cell text-gray-400 text-sm">{p.unidad || '—'}</td>
                    <td className="table-cell text-right font-mono font-bold text-emerald-400">{formatCurrency(p.precio_vigente)}</td>
                    <td className="table-cell text-sm text-gray-500">{p.actualizado_en ? formatDate(p.actualizado_en) : '—'}</td>
                    <td className="table-cell text-right">
                      <button
                        onClick={() => openProductoModal(p)}
                        className="text-xs text-violet-400 hover:text-violet-300 transition-colors"
                      >
                        Editar precio
                      </button>
                    </td>
                  </tr>
                ))}
                {productos.length === 0 && (
                  <tr><td colSpan={5} className="text-center py-6 text-gray-500 text-sm">Sin productos configurados.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tabla de honorarios */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700/60 bg-[#0f172a]/60">
                <th className="table-header">Cliente</th>
                <th className="table-header">Período</th>
                <th className="table-header">Tipo</th>
                <th className="table-header text-right">Importe</th>
                <th className="table-header text-right">Precio ref.</th>
                {isAdmin && <th className="table-header text-right">Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {honorarios.map(h => (
                <tr key={h.id} className="table-row">
                  <td className="table-cell font-medium text-white">{h.client_name}</td>
                  <td className="table-cell text-gray-400">{formatPeriod(h.period)}</td>
                  <td className="table-cell">
                    <span className={h.tipo === 'fijo' ? 'badge-blue' : 'badge-purple'}>
                      {h.tipo === 'fijo' ? 'Fijo' : 'Producto'}
                    </span>
                  </td>
                  <td className="table-cell text-right font-bold text-white">{formatCurrency(h.importe)}</td>
                  <td className="table-cell text-right text-gray-500 text-sm font-mono">
                    {h.precio_producto_snapshot ? formatCurrency(h.precio_producto_snapshot) : '—'}
                  </td>
                  {isAdmin && (
                    <td className="table-cell text-right">
                      <div className="flex gap-3 justify-end">
                        <button
                          title="Configurar honorario"
                          onClick={() => { const c = clients.find(c => c.id === h.client_id); if (c) openConfigModal(c) }}
                          className="text-gray-400 hover:text-white transition-colors"
                        >
                          <Settings size={14} />
                        </button>
                        <button
                          title="Recalcular"
                          onClick={() => handleCalcularOne(h.client_id)}
                          disabled={busy}
                          className="text-violet-400 hover:text-violet-300 transition-colors disabled:opacity-40"
                        >
                          <RefreshCw size={14} />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
              {honorarios.length === 0 && (
                <tr>
                  <td colSpan={isAdmin ? 6 : 5} className="text-center py-12 text-gray-500">
                    No hay honorarios calculados para {formatPeriod(period)}.
                    {isAdmin && ' Hacé clic en "Calcular período" para generarlos.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── MODAL: Producto de referencia ─────────────────────────────────────── */}
      {showProductoModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
          <div className="bg-[#111827] border border-gray-700 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-white">
                {editProducto ? 'Editar producto' : 'Nuevo producto'}
              </h2>
              <button onClick={() => setShowProductoModal(false)} className="text-gray-500 hover:text-white">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleSaveProducto} className="space-y-4">
              <div>
                <label className="label">Nombre *</label>
                <input
                  value={productoForm.nombre}
                  onChange={e => setProductoForm(f => ({ ...f, nombre: e.target.value }))}
                  className="input-field"
                  required
                />
              </div>
              <div>
                <label className="label">Unidad (ej: bolsa, kg, unidad)</label>
                <input
                  value={productoForm.unidad}
                  onChange={e => setProductoForm(f => ({ ...f, unidad: e.target.value }))}
                  className="input-field"
                  placeholder="Opcional"
                />
              </div>
              <div>
                <label className="label">Precio vigente *</label>
                <input
                  type="number"
                  step="0.01"
                  value={productoForm.precio_vigente}
                  onChange={e => setProductoForm(f => ({ ...f, precio_vigente: e.target.value }))}
                  className="input-field font-mono"
                  required
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowProductoModal(false)} className="btn-secondary flex-1 justify-center">Cancelar</button>
                <button type="submit" className="btn-primary flex-1 justify-center">Guardar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODAL: Configurar honorario del cliente ──────────────────────────── */}
      {showConfigModal && configClient && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
          <div className="bg-[#111827] border border-gray-700 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-lg font-bold text-white">Configurar honorario</h2>
                <p className="text-sm text-gray-400">{configClient.name}</p>
              </div>
              <button onClick={() => setShowConfigModal(false)} className="text-gray-500 hover:text-white">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleSaveConfig} className="space-y-4">
              <div>
                <label className="label">Tipo de honorario *</label>
                <select
                  value={configForm.tipo_honorario}
                  onChange={e => setConfigForm(f => ({ ...f, tipo_honorario: e.target.value }))}
                  className="input-field"
                  required
                >
                  <option value="">Seleccionar...</option>
                  <option value="fijo">Fijo mensual</option>
                  <option value="producto">Por producto</option>
                </select>
              </div>

              {configForm.tipo_honorario === 'fijo' && (
                <div>
                  <label className="label">Importe fijo mensual *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={configForm.importe_honorario}
                    onChange={e => setConfigForm(f => ({ ...f, importe_honorario: e.target.value }))}
                    className="input-field font-mono"
                    required
                  />
                </div>
              )}

              {configForm.tipo_honorario === 'producto' && (
                <>
                  <div>
                    <label className="label">Producto de referencia *</label>
                    <select
                      value={configForm.producto_ref_id}
                      onChange={e => setConfigForm(f => ({ ...f, producto_ref_id: e.target.value }))}
                      className="input-field"
                      required
                    >
                      <option value="">Seleccionar...</option>
                      {productos.map(p => (
                        <option key={p.id} value={p.id}>
                          {p.nombre} — {formatCurrency(p.precio_vigente)}/{p.unidad || 'u'}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="label">Cantidad de unidades *</label>
                    <input
                      type="number"
                      step="0.01"
                      value={configForm.cantidad_unidades}
                      onChange={e => setConfigForm(f => ({ ...f, cantidad_unidades: e.target.value }))}
                      className="input-field font-mono"
                      required
                    />
                  </div>
                  {configForm.producto_ref_id && configForm.cantidad_unidades && (
                    <p className="text-sm text-emerald-400 font-mono">
                      Importe estimado:{' '}
                      {formatCurrency(
                        parseFloat(configForm.cantidad_unidades) *
                        (productos.find(p => p.id === parseInt(configForm.producto_ref_id))?.precio_vigente || 0)
                      )}
                    </p>
                  )}
                </>
              )}

              <div>
                <label className="label">Profesional responsable</label>
                <select
                  value={configForm.profesional_id}
                  onChange={e => setConfigForm(f => ({ ...f, profesional_id: e.target.value }))}
                  className="input-field"
                >
                  <option value="">Sin asignar</option>
                  {profesionales.map(p => (
                    <option key={p.id} value={p.id}>{p.nombre}</option>
                  ))}
                </select>
              </div>

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowConfigModal(false)} className="btn-secondary flex-1 justify-center">Cancelar</button>
                <button type="submit" className="btn-primary flex-1 justify-center">Guardar config</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODAL: Actualización cuatrimestral ──────────────────────────────── */}
      {showActModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4 overflow-y-auto py-8">
          <div className="bg-[#111827] border border-gray-700 rounded-2xl p-6 w-full max-w-2xl shadow-2xl">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-white">Actualización cuatrimestral</h2>
              <button onClick={() => { setShowActModal(false); setActPreview(null); setActPct('') }} className="text-gray-500 hover:text-white">
                <X size={18} />
              </button>
            </div>

            <div className="flex gap-3 mb-5">
              <div className="flex-1">
                <label className="label">Índice de actualización (%)</label>
                <input
                  type="number"
                  step="0.01"
                  value={actPct}
                  onChange={e => { setActPct(e.target.value); setActPreview(null) }}
                  placeholder="Ej: 12.5"
                  className="input-field font-mono"
                />
              </div>
              <div className="flex-1">
                <label className="label">Vigente desde</label>
                <input
                  type="month"
                  value={actVigente}
                  onChange={e => setActVigente(e.target.value)}
                  className="input-field"
                />
              </div>
              <div className="flex items-end">
                <button onClick={handlePreviewAct} className="btn-secondary whitespace-nowrap">
                  Ver impacto
                </button>
              </div>
            </div>

            {actPreview && (
              <>
                <div className="overflow-x-auto mb-5">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-700/60 bg-[#0f172a]/60">
                        <th className="table-header">Cliente</th>
                        <th className="table-header">Tipo</th>
                        <th className="table-header text-right">Importe actual</th>
                        <th className="table-header text-right">Importe propuesto</th>
                        <th className="table-header text-center">Aplica</th>
                      </tr>
                    </thead>
                    <tbody>
                      {actPreview.clientes.map(c => (
                        <tr key={c.client_id} className="table-row">
                          <td className="table-cell text-white font-medium">{c.client_name}</td>
                          <td className="table-cell">
                            <span className={c.tipo_honorario === 'fijo' ? 'badge-blue' : 'badge-purple'}>
                              {c.tipo_honorario === 'fijo' ? 'Fijo' : 'Producto'}
                            </span>
                          </td>
                          <td className="table-cell text-right text-gray-400 font-mono">
                            {c.importe_actual != null ? formatCurrency(c.importe_actual) : '—'}
                          </td>
                          <td className="table-cell text-right font-mono font-bold text-emerald-400">
                            {c.importe_propuesto != null ? formatCurrency(c.importe_propuesto) : '—'}
                          </td>
                          <td className="table-cell text-center">
                            {c.aplica_indice
                              ? <span className="text-emerald-400 text-xs">+{actPreview.indice_pct}%</span>
                              : <span className="text-gray-600 text-xs">No aplica</span>
                            }
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex gap-3">
                  <button type="button" onClick={() => { setShowActModal(false); setActPreview(null); setActPct('') }} className="btn-secondary flex-1 justify-center">Cancelar</button>
                  <button onClick={handleAplicarAct} className="btn-primary flex-1 justify-center">
                    Aplicar actualización
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
