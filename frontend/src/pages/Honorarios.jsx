import { useEffect, useState, useMemo } from 'react'
import {
  Plus, DollarSign, Package, Settings, TrendingUp, X, Search,
  Users, UserPlus, CheckCircle2, Loader2,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import { formatCurrency, formatPeriod } from '../utils/helpers'
import {
  getClients, getProductosReferencia, getProfesionales,
  createProducto, updateProducto, configurarHonorario,
  getPreviewActualizacion, aplicarActualizacion,
  getNomina, liquidarNomina, createEmpleado,
} from '../utils/api'

const todayPeriod = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

export default function Honorarios() {
  const { isAdmin } = useAuth()
  const [clients, setClients] = useState([])
  const [productos, setProductos] = useState([])
  const [profesionales, setProfesionales] = useState([])
  const [period, setPeriod] = useState(todayPeriod())
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  // Maestro-detalle: cliente seleccionado + su nómina
  const [selectedClient, setSelectedClient] = useState(null)
  const [nomina, setNomina] = useState(null)
  const [rows, setRows] = useState([])          // [{empleado_id, nombre, apellido, cuil, monto, checked, ya_liquidado, origen_sugerido}]
  const [nominaLoading, setNominaLoading] = useState(false)
  const [liquidating, setLiquidating] = useState(false)
  const [okMsg, setOkMsg] = useState('')

  // Modales
  const [showProductoModal, setShowProductoModal] = useState(false)
  const [editProducto, setEditProducto] = useState(null)
  const [productoForm, setProductoForm] = useState({ nombre: '', unidad: '', precio_vigente: '' })
  const [showProductos, setShowProductos] = useState(false)

  const [showConfigModal, setShowConfigModal] = useState(false)
  const [configClient, setConfigClient] = useState(null)
  const [configForm, setConfigForm] = useState({
    tipo_honorario: '', importe_honorario: '', producto_ref_id: '', cantidad_unidades: '', profesional_id: '',
  })

  const [showEmpModal, setShowEmpModal] = useState(false)
  const [empForm, setEmpForm] = useState({ nombre: '', apellido: '', cuil: '', fecha_ingreso: '' })

  const [showActModal, setShowActModal] = useState(false)
  const [actPct, setActPct] = useState('')
  const [actVigente, setActVigente] = useState(todayPeriod())
  const [actPreview, setActPreview] = useState(null)

  // ─── Carga base ────────────────────────────────────────────────────────────
  const loadBase = () => {
    setLoading(true)
    Promise.all([getClients(), getProductosReferencia(), getProfesionales()])
      .then(([c, p, pr]) => { setClients(c.data); setProductos(p.data); setProfesionales(pr.data) })
      .catch(err => console.error('Honorarios load error:', err))
      .finally(() => setLoading(false))
  }
  useEffect(() => { loadBase() }, [])

  const loadNomina = () => {
    if (!selectedClient) { setNomina(null); setRows([]); return }
    setNominaLoading(true)
    getNomina(selectedClient.id, period)
      .then(r => {
        setNomina(r.data)
        setRows(r.data.empleados.map(e => ({
          ...e,
          monto: String(e.monto_sugerido ?? 0),
          checked: !e.ya_liquidado,   // por defecto, marcar los pendientes
        })))
      })
      .catch(err => { console.error(err); setNomina(null); setRows([]) })
      .finally(() => setNominaLoading(false))
  }
  useEffect(() => { loadNomina(); setOkMsg('') }, [selectedClient, period])

  // ─── Nómina / liquidar ───────────────────────────────────────────────────────
  const allChecked = rows.length > 0 && rows.every(r => r.checked)
  const someChecked = rows.some(r => r.checked)
  const toggleAll = () => setRows(rs => rs.map(r => ({ ...r, checked: !allChecked })))
  const toggleRow = (id) => setRows(rs => rs.map(r => r.empleado_id === id ? { ...r, checked: !r.checked } : r))
  const setRowMonto = (id, v) => setRows(rs => rs.map(r => r.empleado_id === id ? { ...r, monto: v } : r))

  const totalSel = useMemo(
    () => rows.filter(r => r.checked).reduce((acc, r) => acc + (parseFloat(r.monto) || 0), 0),
    [rows]
  )

  const handleLiquidar = async () => {
    const items = rows.filter(r => r.checked).map(r => ({
      empleado_id: r.empleado_id, monto: parseFloat(r.monto) || 0,
    }))
    if (items.length === 0) { alert('Seleccioná al menos un empleado'); return }
    if (!confirm(`¿Liquidar honorarios de ${items.length} empleado(s) para ${formatPeriod(period)} por ${formatCurrency(totalSel)}?`)) return
    setLiquidating(true); setOkMsg('')
    try {
      const res = await liquidarNomina(selectedClient.id, { period, items })
      setOkMsg(`Liquidados ${res.data.liquidados} empleado(s) · total ${formatCurrency(res.data.total)}`)
      loadNomina()
    } catch (e) {
      alert(e.response?.data?.detail || 'Error al liquidar honorarios')
    } finally { setLiquidating(false) }
  }

  // ─── Empleado (alta) ───────────────────────────────────────────────────────
  const handleSaveEmpleado = async (e) => {
    e.preventDefault()
    try {
      await createEmpleado({
        client_id: selectedClient.id,
        nombre: empForm.nombre,
        apellido: empForm.apellido,
        cuil: empForm.cuil || null,
        fecha_ingreso: empForm.fecha_ingreso || null,
      })
      setShowEmpModal(false)
      setEmpForm({ nombre: '', apellido: '', cuil: '', fecha_ingreso: '' })
      loadNomina()
    } catch (e) { alert(e.response?.data?.detail || 'Error al agregar empleado') }
  }

  // ─── Productos ───────────────────────────────────────────────────────────────
  const openProductoModal = (prod = null) => {
    setEditProducto(prod)
    setProductoForm(prod
      ? { nombre: prod.nombre, unidad: prod.unidad || '', precio_vigente: prod.precio_vigente }
      : { nombre: '', unidad: '', precio_vigente: '' })
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
      getProductosReferencia().then(p => setProductos(p.data))
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
      const res = await configurarHonorario(configClient.id, data)
      setShowConfigModal(false)
      // refrescar el cliente en la lista y el seleccionado
      setClients(cs => cs.map(c => c.id === configClient.id ? res.data : c))
      if (selectedClient?.id === configClient.id) { setSelectedClient(res.data); loadNomina() }
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
    if (!confirm(`¿Aplicar actualización de ${actPreview.indice_pct}% vigente desde ${formatPeriod(actVigente)}?`)) return
    try {
      await aplicarActualizacion({
        indice_pct: actPreview.indice_pct,
        vigente_desde: actVigente,
        actualizaciones: actPreview.clientes
          .filter(c => c.aplica_indice)
          .map(c => ({ client_id: c.client_id, nuevo_importe: c.importe_propuesto, confirmar: true })),
      })
      setShowActModal(false); setActPreview(null); setActPct('')
      loadBase()
    } catch (e) { alert(e.response?.data?.detail || 'Error al aplicar actualización') }
  }

  // ─── Render ────────────────────────────────────────────────────────────────
  if (loading) return <div className="min-h-screen flex items-center justify-center"><LoadingSpinner /></div>

  const filteredClients = clients.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase()) || (c.cuit && c.cuit.includes(search)))

  const tipoBadge = (t) => t === 'fijo'
    ? <span className="badge-blue">Fijo</span>
    : t === 'producto' ? <span className="badge-purple">Producto</span>
    : <span className="badge-gray">Sin configurar</span>

  return (
    <div className="page">
      <PageHeader title="Honorarios" subtitle="Liquidación de honorarios del personal por cliente">
        <div className="flex flex-wrap items-center gap-2">
          <input type="month" value={period} onChange={e => setPeriod(e.target.value)} className="input-field w-auto" />
          {isAdmin && (
            <>
              <button onClick={() => setShowProductos(s => !s)} className="btn-secondary">
                <Package size={16} /> Productos
              </button>
              <button onClick={() => setShowActModal(true)} className="btn-secondary">
                <TrendingUp size={16} /> Actualización cuatrimestral
              </button>
            </>
          )}
        </div>
      </PageHeader>

      {/* Productos de referencia (colapsable, admin) */}
      {isAdmin && showProductos && (
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
                <tr className="border-b border-[var(--border)] bg-[var(--surface-2)]">
                  <th className="table-header">Nombre</th>
                  <th className="table-header">Unidad</th>
                  <th className="table-header text-right">Precio vigente</th>
                  <th className="table-header"></th>
                </tr>
              </thead>
              <tbody>
                {productos.map(p => (
                  <tr key={p.id} className="table-row">
                    <td className="table-cell font-medium text-white">{p.nombre}</td>
                    <td className="table-cell text-gray-400 text-sm">{p.unidad || '—'}</td>
                    <td className="table-cell text-right font-mono font-bold text-emerald-400">{formatCurrency(p.precio_vigente)}</td>
                    <td className="table-cell text-right">
                      <button onClick={() => openProductoModal(p)} className="text-xs text-violet-400 hover:text-violet-300">Editar precio</button>
                    </td>
                  </tr>
                ))}
                {productos.length === 0 && (
                  <tr><td colSpan={4} className="text-center py-6 text-gray-500 text-sm">Sin productos configurados.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Maestro-detalle */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Izquierda: clientes */}
        <div className="card p-0 overflow-hidden flex flex-col h-[calc(100vh-14rem)]">
          <div className="p-3 border-b border-[var(--border)]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
              <input
                placeholder="Buscar cliente..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="input-field w-full pl-9"
              />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {filteredClients.map(c => (
              <button
                key={c.id}
                onClick={() => setSelectedClient(c)}
                className={`w-full text-left p-3 rounded-lg transition-colors border ${
                  selectedClient?.id === c.id
                    ? 'bg-violet-600/15 border-violet-500/50'
                    : 'border-transparent hover:bg-white/5'}`}
              >
                <p className="text-sm font-medium text-white truncate">{c.name}</p>
                <div className="flex items-center justify-between mt-0.5">
                  <span className="text-xs text-gray-400 truncate">{c.cuit || 'Sin CUIT'}</span>
                  {tipoBadge(c.tipo_honorario)}
                </div>
              </button>
            ))}
            {filteredClients.length === 0 && (
              <p className="text-center text-gray-500 text-sm py-6">Sin clientes.</p>
            )}
          </div>
        </div>

        {/* Derecha: nómina del cliente */}
        <div className="card p-0 overflow-hidden lg:col-span-2 flex flex-col h-[calc(100vh-14rem)]">
          {!selectedClient ? (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
              <Users size={56} className="mb-3 opacity-20" />
              <p>Seleccioná un cliente para ver su nómina</p>
            </div>
          ) : (
            <>
              <div className="p-4 border-b border-[var(--border)] flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="text-lg font-bold text-white truncate">{selectedClient.name}</h2>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-gray-400">{selectedClient.cuit || 'Sin CUIT'}</span>
                    {tipoBadge(selectedClient.tipo_honorario)}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button onClick={() => setShowEmpModal(true)} className="btn-secondary text-sm py-1.5">
                    <UserPlus size={15} /> Empleado
                  </button>
                  {isAdmin && (
                    <button onClick={() => openConfigModal(selectedClient)} className="btn-icon" title="Configurar honorario (fijo / producto)">
                      <Settings size={18} />
                    </button>
                  )}
                </div>
              </div>

              {okMsg && (
                <div className="mx-4 mt-3 flex items-center gap-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 px-3 py-2 text-sm text-emerald-300">
                  <CheckCircle2 size={16} /> {okMsg}
                </div>
              )}

              <div className="flex-1 overflow-y-auto">
                {nominaLoading ? (
                  <div className="p-8 text-center text-gray-400 text-sm">Cargando nómina…</div>
                ) : rows.length === 0 ? (
                  <div className="p-10 text-center text-gray-500">
                    <Users size={40} className="mx-auto mb-3 opacity-20" />
                    <p className="text-sm">Este cliente no tiene empleados en la nómina.</p>
                    <button onClick={() => setShowEmpModal(true)} className="btn-primary text-sm mt-4">
                      <UserPlus size={15} /> Agregar empleado
                    </button>
                  </div>
                ) : (
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-[var(--border)] bg-[var(--surface-2)]">
                        <th className="table-header w-10 text-center">
                          <input type="checkbox" checked={allChecked} onChange={toggleAll}
                            className="accent-violet-600 w-4 h-4 align-middle" />
                        </th>
                        <th className="table-header">Empleado</th>
                        <th className="table-header">CUIL</th>
                        <th className="table-header text-right">Monto sugerido</th>
                        <th className="table-header text-center">Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map(r => (
                        <tr key={r.empleado_id} className="table-row">
                          <td className="table-cell text-center">
                            <input type="checkbox" checked={r.checked} onChange={() => toggleRow(r.empleado_id)}
                              className="accent-violet-600 w-4 h-4 align-middle" />
                          </td>
                          <td className="table-cell font-medium text-white">{r.apellido}, {r.nombre}</td>
                          <td className="table-cell text-gray-400 font-mono text-xs">{r.cuil || '—'}</td>
                          <td className="table-cell text-right">
                            <div className="flex items-center justify-end gap-1">
                              <span className="text-gray-500 text-xs">$</span>
                              <input
                                type="number" step="0.01"
                                value={r.monto}
                                onChange={e => setRowMonto(r.empleado_id, e.target.value)}
                                className="input-field font-mono text-right py-1 w-32"
                              />
                            </div>
                          </td>
                          <td className="table-cell text-center">
                            {r.ya_liquidado
                              ? <span className="badge-green">Liquidado</span>
                              : r.origen_sugerido === 'periodo_anterior'
                                ? <span className="badge-blue" title="Sugerido del período anterior">Mes ant.</span>
                                : <span className="badge-gray" title="Base de la config del cliente">Base config</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              {rows.length > 0 && (
                <div className="p-4 border-t border-[var(--border)] flex items-center justify-between gap-3">
                  <div className="text-sm text-gray-400">
                    {rows.filter(r => r.checked).length} seleccionado(s) ·{' '}
                    <span className="text-white font-semibold">{formatCurrency(totalSel)}</span>
                  </div>
                  <button onClick={handleLiquidar} disabled={!someChecked || liquidating} className="btn-primary">
                    {liquidating ? <Loader2 size={16} className="animate-spin" /> : <DollarSign size={16} />}
                    Liquidar honorarios
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* ── MODAL: Empleado ───────────────────────────────────────────────────── */}
      {showEmpModal && selectedClient && (
        <div className="modal-backdrop" onClick={() => setShowEmpModal(false)}>
          <div className="modal-panel max-w-md p-6" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2 className="text-lg font-bold text-white">Nuevo empleado</h2>
                <p className="text-sm text-gray-400">{selectedClient.name}</p>
              </div>
              <button onClick={() => setShowEmpModal(false)} className="btn-icon"><X size={18} /></button>
            </div>
            <form onSubmit={handleSaveEmpleado} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Nombre *</label>
                  <input value={empForm.nombre} onChange={e => setEmpForm(f => ({ ...f, nombre: e.target.value }))} className="input-field" required />
                </div>
                <div>
                  <label className="label">Apellido *</label>
                  <input value={empForm.apellido} onChange={e => setEmpForm(f => ({ ...f, apellido: e.target.value }))} className="input-field" required />
                </div>
              </div>
              <div>
                <label className="label">CUIL</label>
                <input value={empForm.cuil} onChange={e => setEmpForm(f => ({ ...f, cuil: e.target.value }))} className="input-field font-mono" placeholder="20-30123456-3" />
              </div>
              <div>
                <label className="label">Fecha de ingreso</label>
                <input type="date" value={empForm.fecha_ingreso} onChange={e => setEmpForm(f => ({ ...f, fecha_ingreso: e.target.value }))} className="input-field" />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowEmpModal(false)} className="btn-secondary flex-1 justify-center">Cancelar</button>
                <button type="submit" className="btn-primary flex-1 justify-center">Agregar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODAL: Producto de referencia ─────────────────────────────────────── */}
      {showProductoModal && (
        <div className="modal-backdrop" onClick={() => setShowProductoModal(false)}>
          <div className="modal-panel max-w-md p-6" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="text-lg font-bold text-white">{editProducto ? 'Editar producto' : 'Nuevo producto'}</h2>
              <button onClick={() => setShowProductoModal(false)} className="btn-icon"><X size={18} /></button>
            </div>
            <form onSubmit={handleSaveProducto} className="space-y-4">
              <div>
                <label className="label">Nombre *</label>
                <input value={productoForm.nombre} onChange={e => setProductoForm(f => ({ ...f, nombre: e.target.value }))} className="input-field" required />
              </div>
              <div>
                <label className="label">Unidad (ej: bolsa, kg, unidad)</label>
                <input value={productoForm.unidad} onChange={e => setProductoForm(f => ({ ...f, unidad: e.target.value }))} className="input-field" placeholder="Opcional" />
              </div>
              <div>
                <label className="label">Precio vigente *</label>
                <input type="number" step="0.01" value={productoForm.precio_vigente} onChange={e => setProductoForm(f => ({ ...f, precio_vigente: e.target.value }))} className="input-field font-mono" required />
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
        <div className="modal-backdrop" onClick={() => setShowConfigModal(false)}>
          <div className="modal-panel max-w-md p-6" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2 className="text-lg font-bold text-white">Configurar honorario</h2>
                <p className="text-sm text-gray-400">{configClient.name}</p>
              </div>
              <button onClick={() => setShowConfigModal(false)} className="btn-icon"><X size={18} /></button>
            </div>
            <form onSubmit={handleSaveConfig} className="space-y-4">
              <div>
                <label className="label">Tipo de honorario *</label>
                <select value={configForm.tipo_honorario} onChange={e => setConfigForm(f => ({ ...f, tipo_honorario: e.target.value }))} className="input-field" required>
                  <option value="">Seleccionar...</option>
                  <option value="fijo">Fijo mensual</option>
                  <option value="producto">Por producto</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">Define el monto base del primer período de cada empleado.</p>
              </div>

              {configForm.tipo_honorario === 'fijo' && (
                <div>
                  <label className="label">Importe fijo mensual *</label>
                  <input type="number" step="0.01" value={configForm.importe_honorario} onChange={e => setConfigForm(f => ({ ...f, importe_honorario: e.target.value }))} className="input-field font-mono" required />
                </div>
              )}

              {configForm.tipo_honorario === 'producto' && (
                <>
                  <div>
                    <label className="label">Producto de referencia *</label>
                    <select value={configForm.producto_ref_id} onChange={e => setConfigForm(f => ({ ...f, producto_ref_id: e.target.value }))} className="input-field" required>
                      <option value="">Seleccionar...</option>
                      {productos.map(p => (
                        <option key={p.id} value={p.id}>{p.nombre} — {formatCurrency(p.precio_vigente)}/{p.unidad || 'u'}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="label">Cantidad de unidades *</label>
                    <input type="number" step="0.01" value={configForm.cantidad_unidades} onChange={e => setConfigForm(f => ({ ...f, cantidad_unidades: e.target.value }))} className="input-field font-mono" required />
                  </div>
                  {configForm.producto_ref_id && configForm.cantidad_unidades && (
                    <p className="text-sm text-emerald-400 font-mono">
                      Base estimada:{' '}
                      {formatCurrency(parseFloat(configForm.cantidad_unidades) * (productos.find(p => p.id === parseInt(configForm.producto_ref_id))?.precio_vigente || 0))}
                    </p>
                  )}
                </>
              )}

              <div>
                <label className="label">Profesional responsable</label>
                <select value={configForm.profesional_id} onChange={e => setConfigForm(f => ({ ...f, profesional_id: e.target.value }))} className="input-field">
                  <option value="">Sin asignar</option>
                  {profesionales.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
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
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 overflow-y-auto"
          onClick={() => { setShowActModal(false); setActPreview(null); setActPct('') }}>
          <div className="modal-panel max-w-2xl mx-auto my-8 p-6" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="text-lg font-bold text-white">Actualización cuatrimestral</h2>
              <button onClick={() => { setShowActModal(false); setActPreview(null); setActPct('') }} className="btn-icon"><X size={18} /></button>
            </div>
            <div className="flex flex-col sm:flex-row gap-3 mb-5">
              <div className="flex-1">
                <label className="label">Índice de actualización (%)</label>
                <input type="number" step="0.01" value={actPct} onChange={e => { setActPct(e.target.value); setActPreview(null) }} placeholder="Ej: 12.5" className="input-field font-mono" />
              </div>
              <div className="flex-1">
                <label className="label">Vigente desde</label>
                <input type="month" value={actVigente} onChange={e => setActVigente(e.target.value)} className="input-field" />
              </div>
              <div className="flex sm:items-end">
                <button onClick={handlePreviewAct} className="btn-secondary whitespace-nowrap w-full sm:w-auto">Ver impacto</button>
              </div>
            </div>
            {actPreview && (
              <>
                <div className="overflow-x-auto mb-5 rounded-lg border border-gray-700/40">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-[var(--border)] bg-[var(--surface-2)]">
                        <th className="table-header whitespace-nowrap">Cliente</th>
                        <th className="table-header whitespace-nowrap">Tipo</th>
                        <th className="table-header text-right whitespace-nowrap">Importe actual</th>
                        <th className="table-header text-right whitespace-nowrap">Propuesto</th>
                        <th className="table-header text-center whitespace-nowrap">Aplica</th>
                      </tr>
                    </thead>
                    <tbody>
                      {actPreview.clientes.map(c => (
                        <tr key={c.client_id} className="table-row">
                          <td className="table-cell text-white font-medium whitespace-nowrap">{c.client_name}</td>
                          <td className="table-cell whitespace-nowrap">
                            <span className={c.tipo_honorario === 'fijo' ? 'badge-blue' : 'badge-purple'}>{c.tipo_honorario === 'fijo' ? 'Fijo' : 'Producto'}</span>
                          </td>
                          <td className="table-cell text-right text-gray-400 font-mono whitespace-nowrap">{c.importe_actual != null ? formatCurrency(c.importe_actual) : '—'}</td>
                          <td className="table-cell text-right font-mono font-bold text-emerald-400 whitespace-nowrap">{c.importe_propuesto != null ? formatCurrency(c.importe_propuesto) : '—'}</td>
                          <td className="table-cell text-center whitespace-nowrap">
                            {c.aplica_indice ? <span className="text-emerald-400 text-xs">+{actPreview.indice_pct}%</span> : <span className="text-gray-600 text-xs">No aplica</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex flex-col sm:flex-row gap-3">
                  <button type="button" onClick={() => { setShowActModal(false); setActPreview(null); setActPct('') }} className="btn-secondary flex-1 justify-center">Cancelar</button>
                  <button onClick={handleAplicarAct} className="btn-primary flex-1 justify-center">Aplicar actualización</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
