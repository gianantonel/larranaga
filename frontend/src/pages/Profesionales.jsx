import { useEffect, useState } from 'react'
import {
  Users, DollarSign, Plus, X, Trash2, Lock, AlertTriangle,
  RefreshCw, ChevronDown,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import StatCard from '../components/UI/StatCard'
import { formatCurrency, formatDate, formatPeriod } from '../utils/helpers'
import {
  getProfesionales, createProfesional, updateProfesional,
  getClients,
  getPagos, createPago, deletePago,
  getLiquidacion, setLiquidacionHonorarios,
  addReintegro, deleteReintegro, cerrarLiquidacion,
} from '../utils/api'

const todayPeriod = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

const FORMA_PAGO = ['efectivo', 'transferencia']

export default function Profesionales() {
  const { isAdmin } = useAuth()
  const [tab, setTab] = useState('liquidaciones') // 'liquidaciones' | 'profesionales'

  // Shared data
  const [profesionales, setProfesionales] = useState([])
  const [clients, setClients] = useState([])
  const [loadingBase, setLoadingBase] = useState(true)

  // Liquidaciones tab
  const [selectedProfId, setSelectedProfId] = useState('')
  const [period, setPeriod] = useState(todayPeriod())
  const [liq, setLiq] = useState(null)
  const [pagos, setPagos] = useState([])
  const [loadingLiq, setLoadingLiq] = useState(false)
  const [honorariosEdit, setHonorariosEdit] = useState('')
  const [savingHon, setSavingHon] = useState(false)

  // Reintegros
  const [reintegroForm, setReintegroForm] = useState({ concepto: '', importe: '' })
  const [savingReintegro, setSavingReintegro] = useState(false)

  // Cerrar mes modal
  const [showCerrarModal, setShowCerrarModal] = useState(false)
  const [cerrarForm, setCerrarForm] = useState({ cobro_efectivo: '0', cobro_transferencia: '0' })

  // Nuevo pago modal
  const [showPagoModal, setShowPagoModal] = useState(false)
  const [pagoForm, setPagoForm] = useState({
    client_id: '', fecha: new Date().toISOString().slice(0, 10),
    importe: '', forma_pago: 'efectivo',
    profesional_destinatario_id: '', notas: '',
  })
  const [savingPago, setSavingPago] = useState(false)

  // Profesionales tab
  const [showProfModal, setShowProfModal] = useState(false)
  const [editProf, setEditProf] = useState(null)
  const [profForm, setProfForm] = useState({ nombre: '', tipo: 'profesional' })

  // ─── Load base data ──────────────────────────────────────────────────────────

  const loadBase = () => {
    setLoadingBase(true)
    Promise.all([getProfesionales(), getClients()])
      .then(([p, c]) => {
        setProfesionales(p.data)
        setClients(c.data)
        if (!selectedProfId && p.data.length > 0) {
          setSelectedProfId(String(p.data[0].id))
        }
      })
      .catch(err => console.error('Profesionales base load error:', err))
      .finally(() => setLoadingBase(false))
  }

  useEffect(() => { loadBase() }, [])

  // ─── Load liquidación ────────────────────────────────────────────────────────

  const loadLiq = () => {
    if (!selectedProfId || !period) return
    setLoadingLiq(true)
    Promise.all([
      getLiquidacion(selectedProfId, period),
      getPagos({ profesional_id: selectedProfId, period }),
    ])
      .then(([l, p]) => {
        setLiq(l.data)
        setHonorariosEdit(l.data.honorarios_totales ?? 0)
        setPagos(p.data)
      })
      .catch(err => console.error('Liquidacion load error:', err))
      .finally(() => setLoadingLiq(false))
  }

  useEffect(() => { if (selectedProfId) loadLiq() }, [selectedProfId, period])

  // ─── Honorarios totales ──────────────────────────────────────────────────────

  const handleSetHonorarios = async () => {
    const val = parseFloat(honorariosEdit)
    if (isNaN(val) || val < 0) { alert('Ingresá un importe válido'); return }
    setSavingHon(true)
    try {
      const res = await setLiquidacionHonorarios(selectedProfId, period, { honorarios_totales: val })
      setLiq(res.data)
    } catch (e) { alert(e.response?.data?.detail || 'Error') }
    finally { setSavingHon(false) }
  }

  // ─── Reintegros ──────────────────────────────────────────────────────────────

  const handleAddReintegro = async (e) => {
    e.preventDefault()
    setSavingReintegro(true)
    try {
      const res = await addReintegro(selectedProfId, period, {
        concepto: reintegroForm.concepto,
        importe: parseFloat(reintegroForm.importe),
      })
      setLiq(res.data)
      setReintegroForm({ concepto: '', importe: '' })
    } catch (e) { alert(e.response?.data?.detail || 'Error al agregar reintegro') }
    finally { setSavingReintegro(false) }
  }

  const handleDeleteReintegro = async (reintegroId) => {
    if (!confirm('¿Eliminar este reintegro?')) return
    try {
      const res = await deleteReintegro(selectedProfId, period, reintegroId)
      setLiq(res.data)
    } catch (e) { alert(e.response?.data?.detail || 'Error') }
  }

  // ─── Cerrar mes ──────────────────────────────────────────────────────────────

  const handleCerrar = async (e) => {
    e.preventDefault()
    try {
      const res = await cerrarLiquidacion(selectedProfId, period, {
        cobro_efectivo: parseFloat(cerrarForm.cobro_efectivo) || 0,
        cobro_transferencia: parseFloat(cerrarForm.cobro_transferencia) || 0,
      })
      setLiq(res.data)
      setShowCerrarModal(false)
    } catch (e) { alert(e.response?.data?.detail || 'Error al cerrar mes') }
  }

  // ─── Pagos ───────────────────────────────────────────────────────────────────

  const handleCreatePago = async (e) => {
    e.preventDefault()
    setSavingPago(true)
    try {
      await createPago({
        client_id: parseInt(pagoForm.client_id),
        fecha: pagoForm.fecha,
        importe: parseFloat(pagoForm.importe),
        forma_pago: pagoForm.forma_pago,
        profesional_destinatario_id: pagoForm.profesional_destinatario_id
          ? parseInt(pagoForm.profesional_destinatario_id) : null,
        notas: pagoForm.notas || null,
      })
      setShowPagoModal(false)
      loadLiq()
    } catch (e) { alert(e.response?.data?.detail || 'Error al registrar pago') }
    finally { setSavingPago(false) }
  }

  const handleDeletePago = async (id) => {
    if (!confirm('¿Eliminar este pago? También se eliminará el movimiento de cuenta corriente asociado.')) return
    try {
      await deletePago(id)
      loadLiq()
    } catch (e) { alert(e.response?.data?.detail || 'Error') }
  }

  // ─── Profesionales CRUD ──────────────────────────────────────────────────────

  const openProfModal = (prof = null) => {
    setEditProf(prof)
    setProfForm(prof ? { nombre: prof.nombre, tipo: prof.tipo } : { nombre: '', tipo: 'profesional' })
    setShowProfModal(true)
  }

  const handleSaveProf = async (e) => {
    e.preventDefault()
    try {
      if (editProf) await updateProfesional(editProf.id, profForm)
      else await createProfesional(profForm)
      setShowProfModal(false)
      loadBase()
    } catch (e) { alert(e.response?.data?.detail || 'Error al guardar profesional') }
  }

  // ─── Render ──────────────────────────────────────────────────────────────────

  if (loadingBase) return <LoadingSpinner text="Cargando profesionales..." />

  const profActivos = profesionales.filter(p => p.activo).length
  const selectedProf = profesionales.find(p => String(p.id) === selectedProfId)
  const totalPagos = pagos.reduce((a, p) => a + p.importe, 0)

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="Profesionales" subtitle="Liquidaciones mensuales y seguimiento de pagos">
        {isAdmin && (
          <div className="flex gap-2">
            <button onClick={() => { setTab('profesionales'); openProfModal() }} className="btn-primary">
              <Plus size={16} /> Nuevo profesional
            </button>
          </div>
        )}
      </PageHeader>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <StatCard title="Profesionales activos" value={profActivos} icon={Users} color="violet" />
        <StatCard title={`Pagos ${formatPeriod(period)}`} value={pagos.length} icon={DollarSign} color="emerald" />
        <StatCard title="Total cobrado" value={formatCurrency(totalPagos)} icon={DollarSign} color="amber" />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-700/40">
        {['liquidaciones', 'profesionales'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium capitalize transition-colors border-b-2 -mb-px ${
              tab === t
                ? 'border-violet-500 text-white'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            {t === 'liquidaciones' ? 'Liquidaciones' : 'Profesionales'}
          </button>
        ))}
      </div>

      {/* ── TAB: LIQUIDACIONES ──────────────────────────────────────────────── */}
      {tab === 'liquidaciones' && (
        <div className="space-y-5">
          {/* Selector */}
          <div className="flex flex-wrap gap-3 items-end">
            <div>
              <label className="label">Profesional</label>
              <select
                value={selectedProfId}
                onChange={e => setSelectedProfId(e.target.value)}
                className="input-field w-auto min-w-[200px]"
              >
                <option value="">Seleccionar...</option>
                {profesionales.map(p => (
                  <option key={p.id} value={p.id}>{p.nombre} ({p.tipo})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Período</label>
              <input
                type="month"
                value={period}
                onChange={e => setPeriod(e.target.value)}
                className="input-field w-auto"
              />
            </div>
            <button onClick={loadLiq} className="btn-secondary" disabled={!selectedProfId}>
              <RefreshCw size={15} />
            </button>
          </div>

          {!selectedProfId && (
            <p className="text-center py-12 text-gray-500">Seleccioná un profesional para ver su liquidación.</p>
          )}

          {selectedProfId && loadingLiq && <LoadingSpinner text="Cargando liquidación..." />}

          {selectedProfId && !loadingLiq && liq && (
            <>
              {/* Liquidación card */}
              <div className="card space-y-5">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-base font-semibold text-white">
                      Liquidación — {selectedProf?.nombre} — {formatPeriod(period)}
                    </h3>
                    {liq.cerrada && (
                      <div className="flex items-center gap-1.5 mt-1">
                        <Lock size={13} className="text-emerald-400" />
                        <span className="text-xs text-emerald-400">
                          Cerrada el {formatDate(liq.cerrada_en)}
                        </span>
                      </div>
                    )}
                  </div>
                  {!liq.cerrada && isAdmin && (
                    <button onClick={() => setShowCerrarModal(true)} className="btn-primary text-sm">
                      <Lock size={14} /> Cerrar mes
                    </button>
                  )}
                </div>

                {liq.alerta_sobreadelanto && (
                  <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 rounded-lg px-3 py-2 text-sm text-amber-300">
                    <AlertTriangle size={15} />
                    Los adelantos percibidos superan el total a cobrar.
                  </div>
                )}

                {/* Honorarios totales */}
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="flex-1">
                      <label className="label">Honorarios totales del período</label>
                      <div className="flex gap-2">
                        <input
                          type="number"
                          step="0.01"
                          value={honorariosEdit}
                          onChange={e => setHonorariosEdit(e.target.value)}
                          disabled={liq.cerrada || !isAdmin}
                          className="input-field font-mono flex-1"
                        />
                        {!liq.cerrada && isAdmin && (
                          <button onClick={handleSetHonorarios} disabled={savingHon} className="btn-secondary whitespace-nowrap">
                            {savingHon ? '...' : 'Actualizar'}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Fórmula */}
                <div className="bg-[#0f172a]/60 rounded-xl p-4 space-y-2 text-sm">
                  <div className="flex justify-between text-gray-300">
                    <span>Honorarios totales</span>
                    <span className="font-mono">{formatCurrency(liq.honorarios_totales)}</span>
                  </div>
                  <div className="flex justify-between text-rose-400">
                    <span>— Adelantos percibidos</span>
                    <span className="font-mono">– {formatCurrency(liq.adelantos_percibidos)}</span>
                  </div>
                  <div className="flex justify-between text-sky-400">
                    <span>+ Saldo anterior</span>
                    <span className="font-mono">+ {formatCurrency(liq.saldo_anterior)}</span>
                  </div>
                  <div className="flex justify-between text-emerald-400">
                    <span>+ Reintegros de gastos</span>
                    <span className="font-mono">+ {formatCurrency(liq.reintegros_gastos)}</span>
                  </div>
                  <div className="border-t border-gray-700/60 pt-2 flex justify-between font-bold text-white">
                    <span>= Total a cobrar</span>
                    <span className="font-mono">{formatCurrency(liq.total_a_cobrar)}</span>
                  </div>
                  {liq.cerrada && (
                    <>
                      <div className="flex justify-between text-gray-300">
                        <span>— Cobro efectivo</span>
                        <span className="font-mono">– {formatCurrency(liq.cobro_efectivo)}</span>
                      </div>
                      <div className="flex justify-between text-gray-300">
                        <span>— Cobro transferencia</span>
                        <span className="font-mono">– {formatCurrency(liq.cobro_transferencia)}</span>
                      </div>
                      <div className={`border-t border-gray-700/60 pt-2 flex justify-between font-bold ${liq.saldo_siguiente >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        <span>= Saldo siguiente</span>
                        <span className="font-mono">{formatCurrency(liq.saldo_siguiente)}</span>
                      </div>
                    </>
                  )}
                </div>

                {/* Reintegros */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-300 mb-2">Reintegros de gastos</h4>
                  {liq.reintegros.length > 0 ? (
                    <div className="space-y-1.5 mb-3">
                      {liq.reintegros.map(r => (
                        <div key={r.id} className="flex items-center justify-between bg-[#0f172a]/40 rounded-lg px-3 py-2 text-sm">
                          <span className="text-gray-300">{r.concepto}</span>
                          <div className="flex items-center gap-3">
                            <span className="font-mono text-emerald-400">{formatCurrency(r.importe)}</span>
                            {!liq.cerrada && isAdmin && (
                              <button onClick={() => handleDeleteReintegro(r.id)} className="text-gray-600 hover:text-rose-400 transition-colors">
                                <Trash2 size={13} />
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-gray-600 mb-3">Sin reintegros registrados.</p>
                  )}

                  {!liq.cerrada && isAdmin && (
                    <form onSubmit={handleAddReintegro} className="flex gap-2">
                      <input
                        value={reintegroForm.concepto}
                        onChange={e => setReintegroForm(f => ({ ...f, concepto: e.target.value }))}
                        placeholder="Concepto (ej: monotributo)"
                        className="input-field flex-1 text-sm"
                        required
                      />
                      <input
                        type="number"
                        step="0.01"
                        value={reintegroForm.importe}
                        onChange={e => setReintegroForm(f => ({ ...f, importe: e.target.value }))}
                        placeholder="Importe"
                        className="input-field w-32 font-mono text-sm"
                        required
                      />
                      <button type="submit" disabled={savingReintegro} className="btn-secondary whitespace-nowrap text-sm">
                        <Plus size={14} /> Agregar
                      </button>
                    </form>
                  )}
                </div>
              </div>

              {/* Pagos del período */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-base font-semibold text-white">
                    Pagos del período — {formatPeriod(period)}
                  </h3>
                  {isAdmin && (
                    <button
                      onClick={() => {
                        setPagoForm({
                          client_id: '', fecha: new Date().toISOString().slice(0, 10),
                          importe: '', forma_pago: 'efectivo',
                          profesional_destinatario_id: selectedProfId, notas: '',
                        })
                        setShowPagoModal(true)
                      }}
                      className="btn-primary text-sm"
                    >
                      <Plus size={15} /> Registrar pago
                    </button>
                  )}
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-700/60 bg-[#0f172a]/60">
                        <th className="table-header">Fecha</th>
                        <th className="table-header">Cliente</th>
                        <th className="table-header">Forma</th>
                        <th className="table-header text-right">Importe</th>
                        <th className="table-header">Notas</th>
                        {isAdmin && <th className="table-header"></th>}
                      </tr>
                    </thead>
                    <tbody>
                      {pagos.map(p => (
                        <tr key={p.id} className="table-row">
                          <td className="table-cell text-gray-300 whitespace-nowrap">{formatDate(p.fecha)}</td>
                          <td className="table-cell font-medium text-white">{p.client_name}</td>
                          <td className="table-cell">
                            <span className={p.forma_pago === 'efectivo' ? 'badge-green' : 'badge-blue'}>
                              {p.forma_pago === 'efectivo' ? 'Efectivo' : 'Transferencia'}
                            </span>
                          </td>
                          <td className="table-cell text-right font-mono font-bold text-white">{formatCurrency(p.importe)}</td>
                          <td className="table-cell text-gray-500 text-xs max-w-[180px] truncate">{p.notas || '—'}</td>
                          {isAdmin && (
                            <td className="table-cell">
                              <button onClick={() => handleDeletePago(p.id)} className="text-gray-600 hover:text-rose-400 transition-colors">
                                <Trash2 size={14} />
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                      {pagos.length === 0 && (
                        <tr><td colSpan={isAdmin ? 6 : 5} className="text-center py-8 text-gray-500">Sin pagos en este período.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* ── TAB: PROFESIONALES ──────────────────────────────────────────────── */}
      {tab === 'profesionales' && (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700/60 bg-[#0f172a]/60">
                  <th className="table-header">Nombre</th>
                  <th className="table-header">Tipo</th>
                  <th className="table-header">Estado</th>
                  <th className="table-header">Alta</th>
                  {isAdmin && <th className="table-header text-right">Acciones</th>}
                </tr>
              </thead>
              <tbody>
                {profesionales.map(p => (
                  <tr key={p.id} className="table-row">
                    <td className="table-cell font-medium text-white">{p.nombre}</td>
                    <td className="table-cell">
                      <span className={p.tipo === 'socio' ? 'badge-purple' : 'badge-blue'}>
                        {p.tipo === 'socio' ? 'Socio' : 'Profesional'}
                      </span>
                    </td>
                    <td className="table-cell">
                      <span className={p.activo ? 'badge-green' : 'badge-red'}>
                        {p.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="table-cell text-sm text-gray-500">{formatDate(p.created_at)}</td>
                    {isAdmin && (
                      <td className="table-cell text-right">
                        <div className="flex gap-3 justify-end">
                          <button
                            onClick={() => openProfModal(p)}
                            className="text-xs text-violet-400 hover:text-violet-300 transition-colors"
                          >
                            Editar
                          </button>
                          {p.activo && (
                            <button
                              onClick={async () => {
                                if (!confirm(`¿Dar de baja a ${p.nombre}?`)) return
                                try { await updateProfesional(p.id, { activo: false }); loadBase() }
                                catch (e) { alert(e.response?.data?.detail || 'Error') }
                              }}
                              className="text-xs text-gray-500 hover:text-rose-400 transition-colors"
                            >
                              Dar de baja
                            </button>
                          )}
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
                {profesionales.length === 0 && (
                  <tr><td colSpan={isAdmin ? 5 : 4} className="text-center py-12 text-gray-500">Sin profesionales registrados.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── MODAL: Cerrar mes ─────────────────────────────────────────────────── */}
      {showCerrarModal && liq && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
          <div className="bg-[#111827] border border-gray-700 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-lg font-bold text-white">Cerrar mes</h2>
                <p className="text-sm text-gray-400">{selectedProf?.nombre} — {formatPeriod(period)}</p>
              </div>
              <button onClick={() => setShowCerrarModal(false)} className="text-gray-500 hover:text-white">
                <X size={18} />
              </button>
            </div>

            <div className="bg-[#0f172a]/60 rounded-xl p-4 mb-5 text-sm space-y-1.5">
              <div className="flex justify-between text-gray-300">
                <span>Total a cobrar</span>
                <span className="font-mono font-bold text-white">{formatCurrency(liq.total_a_cobrar)}</span>
              </div>
            </div>

            <form onSubmit={handleCerrar} className="space-y-4">
              <div>
                <label className="label">Cobro en efectivo</label>
                <input
                  type="number"
                  step="0.01"
                  value={cerrarForm.cobro_efectivo}
                  onChange={e => setCerrarForm(f => ({ ...f, cobro_efectivo: e.target.value }))}
                  className="input-field font-mono"
                />
              </div>
              <div>
                <label className="label">Cobro por transferencia</label>
                <input
                  type="number"
                  step="0.01"
                  value={cerrarForm.cobro_transferencia}
                  onChange={e => setCerrarForm(f => ({ ...f, cobro_transferencia: e.target.value }))}
                  className="input-field font-mono"
                />
              </div>
              <div className="bg-[#0f172a]/60 rounded-xl p-3 text-sm flex justify-between">
                <span className="text-gray-400">Saldo siguiente estimado</span>
                <span className="font-mono font-bold text-emerald-400">
                  {formatCurrency(
                    liq.total_a_cobrar
                    - (parseFloat(cerrarForm.cobro_efectivo) || 0)
                    - (parseFloat(cerrarForm.cobro_transferencia) || 0)
                  )}
                </span>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowCerrarModal(false)} className="btn-secondary flex-1 justify-center">Cancelar</button>
                <button type="submit" className="btn-primary flex-1 justify-center">
                  <Lock size={14} /> Cerrar mes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODAL: Nuevo pago ─────────────────────────────────────────────────── */}
      {showPagoModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
          <div className="bg-[#111827] border border-gray-700 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-white">Registrar pago</h2>
              <button onClick={() => setShowPagoModal(false)} className="text-gray-500 hover:text-white">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleCreatePago} className="space-y-4">
              <div>
                <label className="label">Cliente *</label>
                <select
                  value={pagoForm.client_id}
                  onChange={e => setPagoForm(f => ({ ...f, client_id: e.target.value }))}
                  className="input-field"
                  required
                >
                  <option value="">Seleccionar...</option>
                  {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Fecha *</label>
                  <input
                    type="date"
                    value={pagoForm.fecha}
                    onChange={e => setPagoForm(f => ({ ...f, fecha: e.target.value }))}
                    className="input-field"
                    required
                  />
                </div>
                <div>
                  <label className="label">Importe *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={pagoForm.importe}
                    onChange={e => setPagoForm(f => ({ ...f, importe: e.target.value }))}
                    className="input-field font-mono"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="label">Forma de pago</label>
                <select
                  value={pagoForm.forma_pago}
                  onChange={e => setPagoForm(f => ({ ...f, forma_pago: e.target.value }))}
                  className="input-field"
                >
                  {FORMA_PAGO.map(f => (
                    <option key={f} value={f}>{f.charAt(0).toUpperCase() + f.slice(1)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Profesional destinatario</label>
                <select
                  value={pagoForm.profesional_destinatario_id}
                  onChange={e => setPagoForm(f => ({ ...f, profesional_destinatario_id: e.target.value }))}
                  className="input-field"
                >
                  <option value="">Sin asignar</option>
                  {profesionales.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Notas</label>
                <input
                  value={pagoForm.notas}
                  onChange={e => setPagoForm(f => ({ ...f, notas: e.target.value }))}
                  className="input-field"
                  placeholder="Opcional"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowPagoModal(false)} className="btn-secondary flex-1 justify-center">Cancelar</button>
                <button type="submit" disabled={savingPago} className="btn-primary flex-1 justify-center">
                  {savingPago ? 'Registrando...' : 'Registrar pago'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODAL: Profesional ────────────────────────────────────────────────── */}
      {showProfModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
          <div className="bg-[#111827] border border-gray-700 rounded-2xl p-6 w-full max-w-sm shadow-2xl">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-white">
                {editProf ? 'Editar profesional' : 'Nuevo profesional'}
              </h2>
              <button onClick={() => setShowProfModal(false)} className="text-gray-500 hover:text-white">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleSaveProf} className="space-y-4">
              <div>
                <label className="label">Nombre *</label>
                <input
                  value={profForm.nombre}
                  onChange={e => setProfForm(f => ({ ...f, nombre: e.target.value }))}
                  className="input-field"
                  required
                />
              </div>
              <div>
                <label className="label">Tipo</label>
                <select
                  value={profForm.tipo}
                  onChange={e => setProfForm(f => ({ ...f, tipo: e.target.value }))}
                  className="input-field"
                >
                  <option value="profesional">Profesional</option>
                  <option value="socio">Socio</option>
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowProfModal(false)} className="btn-secondary flex-1 justify-center">Cancelar</button>
                <button type="submit" className="btn-primary flex-1 justify-center">Guardar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
