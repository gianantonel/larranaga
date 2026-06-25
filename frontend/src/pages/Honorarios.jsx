import { useEffect, useState, useMemo } from 'react'
import {
  Plus, DollarSign, Package, TrendingUp, X, Search,
  Users, UserPlus, CheckCircle2, Loader2, Trash2, Wallet,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import { formatCurrency, formatPeriod } from '../utils/helpers'
import {
  getClients, getProductosReferencia,
  createProducto, updateProducto,
  getPreviewActualizacion, aplicarActualizacion,
  getNomina, liquidarNomina, createEmpleado, updateEmpleado,
  registrarPagoEmpleado, eliminarPagoEmpleado,
} from '../utils/api'

const todayPeriod = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}
const todayDate = () => new Date().toISOString().split('T')[0]

const MEDIOS = [
  { v: 'transferencia', l: 'Transferencia' },
  { v: 'efectivo', l: 'Efectivo' },
  { v: 'deposito', l: 'Depósito' },
  { v: 'cheque', l: 'Cheque' },
]

const ESTADO_BADGE = {
  pagado: 'badge-green',
  parcial: 'badge-yellow',
  pendiente: 'badge-blue',
  sin_liquidar: 'badge-gray',
}
const ESTADO_LABEL = {
  pagado: 'Pagado', parcial: 'Parcial', pendiente: 'Pendiente', sin_liquidar: 'Sin liquidar',
}

export default function Honorarios() {
  const { isAdmin } = useAuth()
  const [clients, setClients] = useState([])
  const [productos, setProductos] = useState([])
  const [period, setPeriod] = useState(todayPeriod())
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  const [selectedClient, setSelectedClient] = useState(null)
  const [nomina, setNomina] = useState(null)
  const [rows, setRows] = useState([])
  const [nominaLoading, setNominaLoading] = useState(false)
  const [liquidating, setLiquidating] = useState(false)
  const [okMsg, setOkMsg] = useState('')

  // Modales
  const [showProductoModal, setShowProductoModal] = useState(false)
  const [editProducto, setEditProducto] = useState(null)
  const [productoForm, setProductoForm] = useState({ nombre: '', unidad: '', precio_vigente: '' })
  const [showProductos, setShowProductos] = useState(false)

  const [showEmpModal, setShowEmpModal] = useState(false)
  const [empForm, setEmpForm] = useState({ nombre: '', apellido: '', cuil: '', fecha_ingreso: '' })

  const [pagoRow, setPagoRow] = useState(null)   // fila para el modal de pagos parciales
  const [pagoForm, setPagoForm] = useState({ monto: '', medio_pago: 'transferencia', fecha: todayDate() })

  const [showActModal, setShowActModal] = useState(false)
  const [actPct, setActPct] = useState('')
  const [actVigente, setActVigente] = useState(todayPeriod())
  const [actPreview, setActPreview] = useState(null)

  // ─── Carga ───────────────────────────────────────────────────────────────
  const loadBase = () => {
    setLoading(true)
    Promise.all([getClients(), getProductosReferencia()])
      .then(([c, p]) => { setClients(c.data); setProductos(p.data) })
      .catch(err => console.error('Honorarios load error:', err))
      .finally(() => setLoading(false))
  }
  useEffect(() => { loadBase() }, [])

  const rowFromNomina = (e) => ({
    ...e,
    monto: String(e.monto_a_pagar ?? e.monto_sugerido ?? 0),
    checked: e.estado === 'sin_liquidar',
    modo: e.estado === 'parcial' ? 'parcial' : 'total',
  })

  const loadNomina = () => {
    if (!selectedClient) { setNomina(null); setRows([]); return }
    setNominaLoading(true)
    getNomina(selectedClient.id, period)
      .then(r => { setNomina(r.data); setRows(r.data.empleados.map(rowFromNomina)) })
      .catch(err => { console.error(err); setNomina(null); setRows([]) })
      .finally(() => setNominaLoading(false))
  }
  useEffect(() => { loadNomina(); setOkMsg('') }, [selectedClient, period])

  // ─── Edición de fila / config del empleado ────────────────────────────────
  const patchRow = (id, patch) => setRows(rs => rs.map(r => r.empleado_id === id ? { ...r, ...patch } : r))

  const saveConfig = async (row, patch) => {
    // optimista
    patchRow(row.empleado_id, patch)
    try {
      const { data } = await updateEmpleado(row.empleado_id, patch)
      // recalcular monto sugerido si el período aún no está liquidado
      patchRow(row.empleado_id, {
        medio_pago: data.medio_pago,
        tipo_honorario: data.tipo_honorario,
        importe_fijo: data.importe_fijo,
        producto_ref_id: data.producto_ref_id,
        cantidad_unidades: data.cantidad_unidades,
      })
    } catch (e) { alert(e.response?.data?.detail || 'Error al guardar config del empleado'); loadNomina() }
  }

  const productoPrecio = (id) => productos.find(p => p.id === Number(id))?.precio_vigente || 0
  const baseEmpleado = (row) => row.tipo_honorario === 'producto'
    ? (Number(row.cantidad_unidades) || 0) * productoPrecio(row.producto_ref_id)
    : (Number(row.importe_fijo) || 0)

  // ─── Selección / liquidar ─────────────────────────────────────────────────
  const selectables = rows.filter(r => r.estado !== 'pagado')
  const allChecked = selectables.length > 0 && selectables.every(r => r.checked)
  const someChecked = rows.some(r => r.checked)
  const toggleAll = () => setRows(rs => rs.map(r => r.estado === 'pagado' ? r : { ...r, checked: !allChecked }))
  const toggleRow = (id) => setRows(rs => rs.map(r => r.empleado_id === id ? { ...r, checked: !r.checked } : r))

  const totalSel = useMemo(
    () => rows.filter(r => r.checked).reduce((acc, r) => acc + (parseFloat(r.monto) || 0), 0),
    [rows]
  )

  const handleLiquidar = async () => {
    const items = rows.filter(r => r.checked).map(r => ({
      empleado_id: r.empleado_id,
      monto: parseFloat(r.monto) || 0,
      medio_pago: r.medio_pago || 'transferencia',
      modo: r.modo || 'total',
    }))
    if (items.length === 0) { alert('Seleccioná al menos un empleado'); return }
    if (!confirm(`¿Liquidar ${items.length} empleado(s) para ${formatPeriod(period)} por ${formatCurrency(totalSel)}?`)) return
    setLiquidating(true); setOkMsg('')
    try {
      const res = await liquidarNomina(selectedClient.id, { period, items })
      setOkMsg(`Liquidados ${res.data.liquidados} · total ${formatCurrency(res.data.total)}`)
      loadNomina()
    } catch (e) {
      alert(e.response?.data?.detail || 'Error al liquidar')
    } finally { setLiquidating(false) }
  }

  // ─── Pagos parciales (modal) ──────────────────────────────────────────────
  const openPago = (row) => {
    setPagoRow(row)
    setPagoForm({ monto: String(row.restante ?? ''), medio_pago: row.medio_pago || 'transferencia', fecha: todayDate() })
  }
  const refreshPagoRow = (liq) => {
    // liq = LiquidacionEmpleadoOut devuelto por la API
    patchRow(liq.empleado_id, {
      estado: liq.estado, pagado: liq.pagado, restante: liq.restante,
      pagos: liq.pagos, monto_a_pagar: liq.monto, monto_sugerido: liq.monto,
    })
    setPagoRow(pr => pr ? { ...pr, estado: liq.estado, pagado: liq.pagado, restante: liq.restante, pagos: liq.pagos } : pr)
  }
  const addPago = async (e) => {
    e.preventDefault()
    const monto = parseFloat(pagoForm.monto)
    if (!monto || monto <= 0) { alert('Ingresá un importe válido'); return }
    try {
      const { data } = await registrarPagoEmpleado({
        empleado_id: pagoRow.empleado_id, period,
        monto, medio_pago: pagoForm.medio_pago, fecha: pagoForm.fecha || undefined,
      })
      refreshPagoRow(data)
      setPagoForm(f => ({ ...f, monto: String(data.restante || '') }))
    } catch (e) {
      alert(e.response?.data?.detail?.error || e.response?.data?.detail || 'Error al registrar pago')
    }
  }
  const delPago = async (pagoId) => {
    try { const { data } = await eliminarPagoEmpleado(pagoId); refreshPagoRow(data) }
    catch (e) { alert('Error al eliminar pago') }
  }

  // ─── Empleado (alta) ──────────────────────────────────────────────────────
  const handleSaveEmpleado = async (e) => {
    e.preventDefault()
    try {
      await createEmpleado({
        client_id: selectedClient.id, nombre: empForm.nombre, apellido: empForm.apellido,
        cuil: empForm.cuil || null, fecha_ingreso: empForm.fecha_ingreso || null,
      })
      setShowEmpModal(false); setEmpForm({ nombre: '', apellido: '', cuil: '', fecha_ingreso: '' })
      loadNomina()
    } catch (e) { alert(e.response?.data?.detail || 'Error al agregar empleado') }
  }

  // ─── Productos ────────────────────────────────────────────────────────────
  const openProductoModal = (prod = null) => {
    setEditProducto(prod)
    setProductoForm(prod ? { nombre: prod.nombre, unidad: prod.unidad || '', precio_vigente: prod.precio_vigente }
      : { nombre: '', unidad: '', precio_vigente: '' })
    setShowProductoModal(true)
  }
  const handleSaveProducto = async (e) => {
    e.preventDefault()
    const data = { nombre: productoForm.nombre, unidad: productoForm.unidad || null, precio_vigente: parseFloat(productoForm.precio_vigente) }
    try {
      if (editProducto) await updateProducto(editProducto.id, data); else await createProducto(data)
      setShowProductoModal(false)
      getProductosReferencia().then(p => setProductos(p.data))
    } catch (e) { alert(e.response?.data?.detail || 'Error al guardar producto') }
  }

  // ─── Cuatrimestral ────────────────────────────────────────────────────────
  const handlePreviewAct = async () => {
    const pct = parseFloat(actPct)
    if (isNaN(pct) || pct <= 0) { alert('Ingresá un porcentaje válido mayor a 0'); return }
    try { const res = await getPreviewActualizacion(pct); setActPreview(res.data) }
    catch (e) { alert(e.response?.data?.detail || 'Error al generar vista previa') }
  }
  const handleAplicarAct = async () => {
    if (!actPreview) return
    if (!confirm(`¿Aplicar actualización de ${actPreview.indice_pct}% vigente desde ${formatPeriod(actVigente)}?`)) return
    try {
      await aplicarActualizacion({
        indice_pct: actPreview.indice_pct, vigente_desde: actVigente,
        actualizaciones: actPreview.clientes.filter(c => c.aplica_indice)
          .map(c => ({ client_id: c.client_id, nuevo_importe: c.importe_propuesto, confirmar: true })),
      })
      setShowActModal(false); setActPreview(null); setActPct(''); loadBase()
    } catch (e) { alert(e.response?.data?.detail || 'Error al aplicar actualización') }
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center"><LoadingSpinner /></div>

  const filteredClients = clients.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase()) || (c.cuit && c.cuit.includes(search)))

  return (
    <div className="page">
      <PageHeader title="Honorarios" subtitle="Liquidación de honorarios del personal por cliente">
        <div className="flex flex-wrap items-center gap-2">
          <input type="month" value={period} onChange={e => setPeriod(e.target.value)} className="input-field w-auto" />
          {isAdmin && (
            <>
              <button onClick={() => setShowProductos(s => !s)} className="btn-secondary"><Package size={16} /> Productos</button>
              <button onClick={() => setShowActModal(true)} className="btn-secondary"><TrendingUp size={16} /> Actualización cuatrimestral</button>
            </>
          )}
        </div>
      </PageHeader>

      {isAdmin && showProductos && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-white">Productos de referencia</h3>
            <button className="btn-primary text-sm py-1.5" onClick={() => openProductoModal()}><Plus size={15} /> Nuevo producto</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead><tr className="border-b border-[var(--border)] bg-[var(--surface-2)]">
                <th className="table-header">Nombre</th><th className="table-header">Unidad</th>
                <th className="table-header text-right">Precio vigente</th><th className="table-header"></th>
              </tr></thead>
              <tbody>
                {productos.map(p => (
                  <tr key={p.id} className="table-row">
                    <td className="table-cell font-medium text-white">{p.nombre}</td>
                    <td className="table-cell text-gray-400 text-sm">{p.unidad || '—'}</td>
                    <td className="table-cell text-right font-mono font-bold text-emerald-400">{formatCurrency(p.precio_vigente)}</td>
                    <td className="table-cell text-right"><button onClick={() => openProductoModal(p)} className="text-xs text-violet-400 hover:text-violet-300">Editar precio</button></td>
                  </tr>
                ))}
                {productos.length === 0 && <tr><td colSpan={4} className="text-center py-6 text-gray-500 text-sm">Sin productos.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Clientes */}
        <div className="card p-0 overflow-hidden flex flex-col h-[calc(100vh-14rem)]">
          <div className="p-3 border-b border-[var(--border)]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
              <input placeholder="Buscar cliente..." value={search} onChange={e => setSearch(e.target.value)} className="input-field w-full pl-9" />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {filteredClients.map(c => (
              <button key={c.id} onClick={() => setSelectedClient(c)}
                className={`w-full text-left p-3 rounded-lg transition-colors border ${selectedClient?.id === c.id ? 'bg-violet-600/15 border-violet-500/50' : 'border-transparent hover:bg-white/5'}`}>
                <p className="text-sm font-medium text-white truncate">{c.name}</p>
                <span className="text-xs text-gray-400 truncate">{c.cuit || 'Sin CUIT'}</span>
              </button>
            ))}
            {filteredClients.length === 0 && <p className="text-center text-gray-500 text-sm py-6">Sin clientes.</p>}
          </div>
        </div>

        {/* Nómina */}
        <div className="card p-0 overflow-hidden lg:col-span-2 flex flex-col h-[calc(100vh-14rem)]">
          {!selectedClient ? (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
              <Users size={56} className="mb-3 opacity-20" /><p>Seleccioná un cliente para ver su nómina</p>
            </div>
          ) : (
            <>
              <div className="p-4 border-b border-[var(--border)] flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="text-lg font-bold text-white truncate">{selectedClient.name}</h2>
                  <span className="text-xs text-gray-400">{selectedClient.cuit || 'Sin CUIT'}</span>
                </div>
                <button onClick={() => setShowEmpModal(true)} className="btn-secondary text-sm py-1.5 shrink-0"><UserPlus size={15} /> Empleado</button>
              </div>

              {okMsg && (
                <div className="mx-4 mt-3 flex items-center gap-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 px-3 py-2 text-sm text-emerald-300">
                  <CheckCircle2 size={16} /> {okMsg}
                </div>
              )}

              <div className="flex-1 overflow-y-auto p-3 space-y-2">
                {nominaLoading ? (
                  <div className="p-8 text-center text-gray-400 text-sm">Cargando nómina…</div>
                ) : rows.length === 0 ? (
                  <div className="p-10 text-center text-gray-500">
                    <Users size={40} className="mx-auto mb-3 opacity-20" />
                    <p className="text-sm">Este cliente no tiene empleados en la nómina.</p>
                    <button onClick={() => setShowEmpModal(true)} className="btn-primary text-sm mt-4"><UserPlus size={15} /> Agregar empleado</button>
                  </div>
                ) : (
                  <>
                    <label className="flex items-center gap-2 px-1 text-xs text-gray-400">
                      <input type="checkbox" checked={allChecked} onChange={toggleAll} className="accent-violet-600 w-4 h-4" />
                      Seleccionar todos
                    </label>
                    {rows.map(r => (
                      <div key={r.empleado_id} className={`rounded-xl border p-3 ${r.checked ? 'border-violet-500/40 bg-violet-600/5' : 'border-[var(--border)]'}`}>
                        <div className="flex items-center justify-between gap-2">
                          <label className="flex items-center gap-2 min-w-0">
                            <input type="checkbox" checked={r.checked} disabled={r.estado === 'pagado'}
                              onChange={() => toggleRow(r.empleado_id)} className="accent-violet-600 w-4 h-4 shrink-0 disabled:opacity-40" />
                            <span className="font-medium text-white truncate">{r.apellido}, {r.nombre}</span>
                            <span className="text-xs text-gray-500 font-mono shrink-0">{r.cuil || ''}</span>
                          </label>
                          <span className={ESTADO_BADGE[r.estado]}>{ESTADO_LABEL[r.estado]}</span>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-3">
                          {/* Medio de pago */}
                          <div>
                            <label className="text-[11px] text-gray-500 block mb-0.5">Medio de pago</label>
                            <select value={r.medio_pago} onChange={e => saveConfig(r, { medio_pago: e.target.value })} className="input-field py-1 text-sm w-full">
                              {MEDIOS.map(m => <option key={m.v} value={m.v}>{m.l}</option>)}
                            </select>
                          </div>
                          {/* Tipo fijo/producto */}
                          <div>
                            <label className="text-[11px] text-gray-500 block mb-0.5">Honorario</label>
                            <div className="flex items-center gap-2 text-sm h-[34px]">
                              <label className="flex items-center gap-1 cursor-pointer">
                                <input type="radio" name={`tipo-${r.empleado_id}`} checked={r.tipo_honorario === 'fijo'}
                                  onChange={() => saveConfig(r, { tipo_honorario: 'fijo' })} className="accent-violet-600" /> Fijo
                              </label>
                              <label className="flex items-center gap-1 cursor-pointer">
                                <input type="radio" name={`tipo-${r.empleado_id}`} checked={r.tipo_honorario === 'producto'}
                                  onChange={() => saveConfig(r, { tipo_honorario: 'producto' })} className="accent-violet-600" /> Producto
                              </label>
                            </div>
                          </div>
                          {/* Config según tipo */}
                          {r.tipo_honorario === 'producto' ? (
                            <>
                              <div>
                                <label className="text-[11px] text-gray-500 block mb-0.5">Producto</label>
                                <select value={r.producto_ref_id || ''} onChange={e => saveConfig(r, { producto_ref_id: e.target.value ? Number(e.target.value) : null })} className="input-field py-1 text-sm w-full">
                                  <option value="">—</option>
                                  {productos.map(p => <option key={p.id} value={p.id}>{p.nombre} ({formatCurrency(p.precio_vigente)})</option>)}
                                </select>
                              </div>
                              <div>
                                <label className="text-[11px] text-gray-500 block mb-0.5">Cantidad</label>
                                <input type="number" step="0.01" defaultValue={r.cantidad_unidades ?? ''}
                                  onBlur={e => saveConfig(r, { cantidad_unidades: e.target.value ? Number(e.target.value) : null })}
                                  className="input-field py-1 text-sm font-mono w-full" />
                              </div>
                            </>
                          ) : (
                            <div className="md:col-span-2">
                              <label className="text-[11px] text-gray-500 block mb-0.5">Importe fijo</label>
                              <input type="number" step="0.01" defaultValue={r.importe_fijo ?? ''}
                                onBlur={e => saveConfig(r, { importe_fijo: e.target.value ? Number(e.target.value) : null })}
                                className="input-field py-1 text-sm font-mono w-full" />
                            </div>
                          )}
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2 items-end">
                          {/* Monto a pagar */}
                          <div>
                            <label className="text-[11px] text-gray-500 block mb-0.5">Monto a pagar {r.origen_sugerido === 'periodo_anterior' && <span className="text-violet-400">(mes ant.)</span>}</label>
                            <input type="number" step="0.01" value={r.monto} disabled={r.estado !== 'sin_liquidar'}
                              onChange={e => patchRow(r.empleado_id, { monto: e.target.value })}
                              className="input-field py-1 text-sm font-mono w-full disabled:opacity-60" />
                          </div>
                          {/* Total / Parcial */}
                          <div>
                            <label className="text-[11px] text-gray-500 block mb-0.5">Pago</label>
                            <div className="flex items-center gap-2 text-sm h-[34px]">
                              <label className="flex items-center gap-1 cursor-pointer">
                                <input type="radio" name={`modo-${r.empleado_id}`} checked={r.modo === 'total'} disabled={r.estado !== 'sin_liquidar'}
                                  onChange={() => patchRow(r.empleado_id, { modo: 'total' })} className="accent-violet-600" /> Total
                              </label>
                              <label className="flex items-center gap-1 cursor-pointer">
                                <input type="radio" name={`modo-${r.empleado_id}`} checked={r.modo === 'parcial'} disabled={r.estado !== 'sin_liquidar'}
                                  onChange={() => patchRow(r.empleado_id, { modo: 'parcial' })} className="accent-violet-600" /> Parcial
                              </label>
                            </div>
                          </div>
                          {/* Estado pagos / gestionar */}
                          <div className="md:col-span-2 flex items-center justify-end gap-3">
                            {r.estado !== 'sin_liquidar' && (
                              <span className="text-xs text-gray-400">
                                Pagado <b className="text-white">{formatCurrency(r.pagado)}</b>
                                {r.restante > 0 && <> · resta <b className="text-amber-300">{formatCurrency(r.restante)}</b></>}
                              </span>
                            )}
                            {r.liquidacion_id && r.estado !== 'pagado' && (
                              <button onClick={() => openPago(r)} className="btn-secondary text-sm py-1"><Wallet size={14} /> Pagos</button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </>
                )}
              </div>

              {rows.length > 0 && (
                <div className="p-4 border-t border-[var(--border)] flex items-center justify-between gap-3">
                  <div className="text-sm text-gray-400">{rows.filter(r => r.checked).length} seleccionado(s) · <span className="text-white font-semibold">{formatCurrency(totalSel)}</span></div>
                  <button onClick={handleLiquidar} disabled={!someChecked || liquidating} className="btn-primary">
                    {liquidating ? <Loader2 size={16} className="animate-spin" /> : <DollarSign size={16} />} Liquidar honorarios
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* ── MODAL: Pagos parciales ───────────────────────────────────────────── */}
      {pagoRow && (
        <div className="modal-backdrop" onClick={() => setPagoRow(null)}>
          <div className="modal-panel max-w-lg p-6" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2 className="text-lg font-bold text-white">Pagos parciales</h2>
                <p className="text-sm text-gray-400">{pagoRow.apellido}, {pagoRow.nombre} · {formatPeriod(period)}</p>
              </div>
              <button onClick={() => setPagoRow(null)} className="btn-icon"><X size={18} /></button>
            </div>

            <div className="grid grid-cols-3 gap-2 mb-4 text-center">
              <div className="rounded-lg bg-white/5 p-2"><p className="text-[11px] text-gray-500">Total</p><p className="font-mono font-bold text-white">{formatCurrency(pagoRow.monto_a_pagar)}</p></div>
              <div className="rounded-lg bg-emerald-500/10 p-2"><p className="text-[11px] text-gray-500">Pagado</p><p className="font-mono font-bold text-emerald-300">{formatCurrency(pagoRow.pagado)}</p></div>
              <div className="rounded-lg bg-amber-500/10 p-2"><p className="text-[11px] text-gray-500">Restante</p><p className="font-mono font-bold text-amber-300">{formatCurrency(pagoRow.restante)}</p></div>
            </div>

            <div className="space-y-1 mb-4 max-h-48 overflow-y-auto">
              {(pagoRow.pagos || []).length === 0 && <p className="text-sm text-gray-500 text-center py-3">Todavía no hay pagos.</p>}
              {(pagoRow.pagos || []).map(p => (
                <div key={p.id} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2 text-sm">
                  <span className="font-mono font-medium text-white">{formatCurrency(p.monto)}</span>
                  <span className="text-gray-400 capitalize">{p.medio_pago}</span>
                  <span className="text-gray-500 text-xs">{p.fecha}</span>
                  <button onClick={() => delPago(p.id)} className="text-gray-500 hover:text-rose-400"><Trash2 size={14} /></button>
                </div>
              ))}
            </div>

            {pagoRow.restante > 0 ? (
              <form onSubmit={addPago} className="grid grid-cols-1 sm:grid-cols-4 gap-2 items-end border-t border-[var(--border)] pt-4">
                <div>
                  <label className="text-[11px] text-gray-500 block mb-0.5">Importe</label>
                  <input type="number" step="0.01" value={pagoForm.monto} onChange={e => setPagoForm(f => ({ ...f, monto: e.target.value }))} className="input-field py-1.5 text-sm font-mono w-full" required />
                </div>
                <div>
                  <label className="text-[11px] text-gray-500 block mb-0.5">Medio</label>
                  <select value={pagoForm.medio_pago} onChange={e => setPagoForm(f => ({ ...f, medio_pago: e.target.value }))} className="input-field py-1.5 text-sm w-full">
                    {MEDIOS.map(m => <option key={m.v} value={m.v}>{m.l}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-[11px] text-gray-500 block mb-0.5">Fecha</label>
                  <input type="date" value={pagoForm.fecha} onChange={e => setPagoForm(f => ({ ...f, fecha: e.target.value }))} className="input-field py-1.5 text-sm w-full" />
                </div>
                <button type="submit" className="btn-primary justify-center"><Plus size={15} /> Pago</button>
              </form>
            ) : (
              <div className="flex items-center justify-center gap-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 px-3 py-2 text-sm text-emerald-300">
                <CheckCircle2 size={16} /> Pago completo
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── MODAL: Empleado ─────────────────────────────────────────────────── */}
      {showEmpModal && selectedClient && (
        <div className="modal-backdrop" onClick={() => setShowEmpModal(false)}>
          <div className="modal-panel max-w-md p-6" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div><h2 className="text-lg font-bold text-white">Nuevo empleado</h2><p className="text-sm text-gray-400">{selectedClient.name}</p></div>
              <button onClick={() => setShowEmpModal(false)} className="btn-icon"><X size={18} /></button>
            </div>
            <form onSubmit={handleSaveEmpleado} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div><label className="label">Nombre *</label><input value={empForm.nombre} onChange={e => setEmpForm(f => ({ ...f, nombre: e.target.value }))} className="input-field" required /></div>
                <div><label className="label">Apellido *</label><input value={empForm.apellido} onChange={e => setEmpForm(f => ({ ...f, apellido: e.target.value }))} className="input-field" required /></div>
              </div>
              <div><label className="label">CUIL</label><input value={empForm.cuil} onChange={e => setEmpForm(f => ({ ...f, cuil: e.target.value }))} className="input-field font-mono" placeholder="20-30123456-3" /></div>
              <div><label className="label">Fecha de ingreso</label><input type="date" value={empForm.fecha_ingreso} onChange={e => setEmpForm(f => ({ ...f, fecha_ingreso: e.target.value }))} className="input-field" /></div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowEmpModal(false)} className="btn-secondary flex-1 justify-center">Cancelar</button>
                <button type="submit" className="btn-primary flex-1 justify-center">Agregar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODAL: Producto ─────────────────────────────────────────────────── */}
      {showProductoModal && (
        <div className="modal-backdrop" onClick={() => setShowProductoModal(false)}>
          <div className="modal-panel max-w-md p-6" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="text-lg font-bold text-white">{editProducto ? 'Editar producto' : 'Nuevo producto'}</h2>
              <button onClick={() => setShowProductoModal(false)} className="btn-icon"><X size={18} /></button>
            </div>
            <form onSubmit={handleSaveProducto} className="space-y-4">
              <div><label className="label">Nombre *</label><input value={productoForm.nombre} onChange={e => setProductoForm(f => ({ ...f, nombre: e.target.value }))} className="input-field" required /></div>
              <div><label className="label">Unidad</label><input value={productoForm.unidad} onChange={e => setProductoForm(f => ({ ...f, unidad: e.target.value }))} className="input-field" placeholder="Opcional" /></div>
              <div><label className="label">Precio vigente *</label><input type="number" step="0.01" value={productoForm.precio_vigente} onChange={e => setProductoForm(f => ({ ...f, precio_vigente: e.target.value }))} className="input-field font-mono" required /></div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowProductoModal(false)} className="btn-secondary flex-1 justify-center">Cancelar</button>
                <button type="submit" className="btn-primary flex-1 justify-center">Guardar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODAL: Actualización cuatrimestral ──────────────────────────────── */}
      {showActModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 overflow-y-auto" onClick={() => { setShowActModal(false); setActPreview(null); setActPct('') }}>
          <div className="modal-panel max-w-2xl mx-auto my-8 p-6" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="text-lg font-bold text-white">Actualización cuatrimestral</h2>
              <button onClick={() => { setShowActModal(false); setActPreview(null); setActPct('') }} className="btn-icon"><X size={18} /></button>
            </div>
            <div className="flex flex-col sm:flex-row gap-3 mb-5">
              <div className="flex-1"><label className="label">Índice (%)</label><input type="number" step="0.01" value={actPct} onChange={e => { setActPct(e.target.value); setActPreview(null) }} placeholder="Ej: 12.5" className="input-field font-mono" /></div>
              <div className="flex-1"><label className="label">Vigente desde</label><input type="month" value={actVigente} onChange={e => setActVigente(e.target.value)} className="input-field" /></div>
              <div className="flex sm:items-end"><button onClick={handlePreviewAct} className="btn-secondary whitespace-nowrap w-full sm:w-auto">Ver impacto</button></div>
            </div>
            {actPreview && (
              <>
                <div className="overflow-x-auto mb-5 rounded-lg border border-gray-700/40">
                  <table className="w-full text-sm">
                    <thead><tr className="border-b border-[var(--border)] bg-[var(--surface-2)]">
                      <th className="table-header">Cliente</th><th className="table-header">Tipo</th>
                      <th className="table-header text-right">Actual</th><th className="table-header text-right">Propuesto</th><th className="table-header text-center">Aplica</th>
                    </tr></thead>
                    <tbody>
                      {actPreview.clientes.map(c => (
                        <tr key={c.client_id} className="table-row">
                          <td className="table-cell text-white font-medium">{c.client_name}</td>
                          <td className="table-cell"><span className={c.tipo_honorario === 'fijo' ? 'badge-blue' : 'badge-purple'}>{c.tipo_honorario === 'fijo' ? 'Fijo' : 'Producto'}</span></td>
                          <td className="table-cell text-right text-gray-400 font-mono">{c.importe_actual != null ? formatCurrency(c.importe_actual) : '—'}</td>
                          <td className="table-cell text-right font-mono font-bold text-emerald-400">{c.importe_propuesto != null ? formatCurrency(c.importe_propuesto) : '—'}</td>
                          <td className="table-cell text-center">{c.aplica_indice ? <span className="text-emerald-400 text-xs">+{actPreview.indice_pct}%</span> : <span className="text-gray-600 text-xs">No aplica</span>}</td>
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
