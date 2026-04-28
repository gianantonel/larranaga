import { useState, useEffect } from 'react'
import api from '../utils/api'
import { RefreshCw, Plus, Trash2, ChevronDown, ChevronRight, AlertCircle, Check, Lock, Unlock } from 'lucide-react'

const MONTHS = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

function getPeriodo() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

function formatARS(n) {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', minimumFractionDigits: 0 }).format(n || 0)
}

// ─── Modal crear liquidación ──────────────────────────────────────────────────

function NuevaLiquidacionModal({ profId, periodo, onClose, onCreated }) {
  const [honorarios, setHonorarios] = useState('')
  const [saldoAnterior, setSaldoAnterior] = useState(0)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleCreate() {
    if (!honorarios) return
    setSaving(true)
    setError('')
    try {
      await api.post(`/profesionales/${profId}/liquidaciones`, {
        profesional_id: profId,
        periodo,
        honorarios_totales: Number(honorarios),
        saldo_anterior: Number(saldoAnterior),
      })
      onCreated()
      onClose()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1e293b] rounded-2xl border border-gray-700/50 w-full max-w-sm shadow-2xl">
        <div className="px-6 py-4 border-b border-gray-700/40">
          <h3 className="text-lg font-semibold text-white">Nueva Liquidación</h3>
          <p className="text-sm text-gray-400 mt-0.5">Período {periodo}</p>
        </div>
        <div className="px-6 py-5 space-y-4">
          <div>
            <label className="block text-sm text-gray-300 mb-1.5">Total honorarios del mes ($)</label>
            <input
              type="number"
              value={honorarios}
              onChange={e => setHonorarios(e.target.value)}
              className="w-full bg-[#0f172a] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-500"
              placeholder="1950000"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-sm text-gray-300 mb-1.5">Saldo mes anterior ($)</label>
            <input
              type="number"
              value={saldoAnterior}
              onChange={e => setSaldoAnterior(e.target.value)}
              className="w-full bg-[#0f172a] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-500"
              placeholder="0"
            />
            <p className="text-xs text-gray-500 mt-1">Positivo = monto a favor del profesional. Negativo = cobró de más.</p>
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
        </div>
        <div className="px-6 py-4 border-t border-gray-700/40 flex gap-3 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancelar</button>
          <button
            onClick={handleCreate}
            disabled={saving || !honorarios}
            className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium disabled:opacity-50"
          >
            {saving ? 'Creando...' : 'Crear'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Card de liquidación de un profesional ────────────────────────────────────

function LiquidacionCard({ liq, onRefresh }) {
  const [expanded, setExpanded] = useState(false)
  const [newReintegro, setNewReintegro] = useState({ concepto: '', importe: '' })
  const [addingReintegro, setAddingReintegro] = useState(false)
  const [editForma, setEditForma] = useState(false)
  const [forma, setForma] = useState(liq.forma_cobro || '')
  const [monto, setMonto] = useState(liq.monto_cobrado || 0)
  const [saving, setSaving] = useState(false)
  const [syncing, setSyncing] = useState(false)

  async function addReintegro() {
    if (!newReintegro.concepto || !newReintegro.importe) return
    setAddingReintegro(true)
    try {
      await api.post(`/profesionales/liquidaciones/${liq.id}/reintegros`, {
        concepto: newReintegro.concepto,
        importe: Number(newReintegro.importe),
      })
      setNewReintegro({ concepto: '', importe: '' })
      onRefresh()
    } catch { /* ignore */ }
    finally { setAddingReintegro(false) }
  }

  async function deleteReintegro(rId) {
    try {
      await api.delete(`/profesionales/liquidaciones/${liq.id}/reintegros/${rId}`)
      onRefresh()
    } catch { /* ignore */ }
  }

  async function saveCobro() {
    setSaving(true)
    try {
      await api.patch(`/profesionales/liquidaciones/${liq.id}`, {
        forma_cobro: forma,
        monto_cobrado: Number(monto),
      })
      setEditForma(false)
      onRefresh()
    } catch { /* ignore */ }
    finally { setSaving(false) }
  }

  async function syncAdelantos() {
    setSyncing(true)
    try {
      await api.post(`/profesionales/liquidaciones/${liq.id}/sincronizar-adelantos`)
      onRefresh()
    } catch { /* ignore */ }
    finally { setSyncing(false) }
  }

  async function toggleCerrada() {
    try {
      await api.patch(`/profesionales/liquidaciones/${liq.id}`, { cerrada: !liq.cerrada })
      onRefresh()
    } catch { /* ignore */ }
  }

  const saldoColor = liq.saldo_siguiente > 0
    ? 'text-yellow-400'
    : liq.saldo_siguiente < 0
    ? 'text-green-400'
    : 'text-gray-300'

  return (
    <div className={`bg-[#1e293b] rounded-2xl border overflow-hidden transition-colors ${
      liq.cerrada ? 'border-gray-700/20 opacity-70' : 'border-gray-700/40'
    }`}>
      {/* Header colapsable */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full px-5 py-4 flex items-center gap-4 hover:bg-white/3 transition-colors text-left"
      >
        {expanded ? <ChevronDown size={16} className="text-gray-400 flex-shrink-0" /> : <ChevronRight size={16} className="text-gray-400 flex-shrink-0" />}
        <div className="flex-1 grid grid-cols-4 gap-4 items-center">
          <div>
            <p className="text-white font-semibold">{liq.profesional_nombre}</p>
            {liq.cerrada && <span className="text-xs text-gray-500">Cerrada</span>}
          </div>
          <div>
            <p className="text-xs text-gray-400">Honorarios</p>
            <p className="text-white font-medium">{formatARS(liq.honorarios_totales)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400">Total a cobrar</p>
            <p className="text-violet-300 font-semibold">{formatARS(liq.total_a_cobrar)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400">Saldo próximo mes</p>
            <p className={`font-semibold ${saldoColor}`}>{formatARS(liq.saldo_siguiente)}</p>
          </div>
        </div>
      </button>

      {/* Detalle expandido */}
      {expanded && (
        <div className="border-t border-gray-700/40 px-5 py-5 space-y-5">
          {/* Tabla resumen */}
          <div className="bg-[#0f172a] rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <tbody>
                {[
                  ['Honorarios del mes', liq.honorarios_totales, 'text-white'],
                  ['Adelantos percibidos', -liq.adelantos_percibidos, 'text-red-400'],
                  ['Saldo mes anterior', liq.saldo_anterior, liq.saldo_anterior >= 0 ? 'text-yellow-400' : 'text-green-400'],
                  ['Reintegro de gastos', liq.reintegro_gastos, 'text-blue-400'],
                ].map(([label, val, color]) => (
                  <tr key={label} className="border-b border-gray-700/20">
                    <td className="px-4 py-2 text-gray-400">{label}</td>
                    <td className={`px-4 py-2 text-right font-medium ${color}`}>{formatARS(Math.abs(val))}{val < 0 ? ' (−)' : ''}</td>
                  </tr>
                ))}
                <tr className="bg-violet-500/10">
                  <td className="px-4 py-2 text-white font-semibold">TOTAL A COBRAR</td>
                  <td className="px-4 py-2 text-right text-violet-300 font-bold text-base">{formatARS(liq.total_a_cobrar)}</td>
                </tr>
                <tr className="border-t border-gray-700/20">
                  <td className="px-4 py-2 text-gray-400">Cobrado ({liq.forma_cobro || '—'})</td>
                  <td className={`px-4 py-2 text-right font-medium ${liq.monto_cobrado > 0 ? 'text-green-400' : 'text-gray-500'}`}>{formatARS(liq.monto_cobrado)}</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 text-gray-400">Saldo a favor próximo mes</td>
                  <td className={`px-4 py-2 text-right font-bold ${saldoColor}`}>{formatARS(liq.saldo_siguiente)}</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Reintegros */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-gray-300">Reintegro de gastos</h4>
              <button
                onClick={syncAdelantos}
                disabled={syncing}
                className="flex items-center gap-1 text-xs text-gray-400 hover:text-violet-300 transition-colors"
              >
                <RefreshCw size={12} className={syncing ? 'animate-spin' : ''} />
                Sincronizar adelantos
              </button>
            </div>
            <div className="space-y-2 mb-3">
              {liq.reintegros.map(r => (
                <div key={r.id} className="flex items-center gap-3 bg-white/5 rounded-lg px-3 py-2">
                  <p className="flex-1 text-sm text-gray-300">{r.concepto}</p>
                  <p className="text-sm text-blue-400 font-medium">{formatARS(r.importe)}</p>
                  {!liq.cerrada && (
                    <button onClick={() => deleteReintegro(r.id)} className="text-gray-600 hover:text-red-400 transition-colors">
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              ))}
              {liq.reintegros.length === 0 && (
                <p className="text-xs text-gray-500 italic">Sin reintegros</p>
              )}
            </div>
            {!liq.cerrada && (
              <div className="flex gap-2">
                <input
                  value={newReintegro.concepto}
                  onChange={e => setNewReintegro(r => ({ ...r, concepto: e.target.value }))}
                  placeholder="Concepto (ej: Monotributo)"
                  className="flex-1 bg-[#0f172a] border border-gray-600 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-violet-500"
                />
                <input
                  type="number"
                  value={newReintegro.importe}
                  onChange={e => setNewReintegro(r => ({ ...r, importe: e.target.value }))}
                  placeholder="Importe"
                  className="w-28 bg-[#0f172a] border border-gray-600 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-violet-500"
                />
                <button
                  onClick={addReintegro}
                  disabled={addingReintegro || !newReintegro.concepto || !newReintegro.importe}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm disabled:opacity-50 transition-colors"
                >
                  <Plus size={14} />
                </button>
              </div>
            )}
          </div>

          {/* Cobro */}
          {!liq.cerrada && (
            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-3">Registrar cobro</h4>
              {editForma ? (
                <div className="flex gap-2 items-end">
                  <div className="flex-1 space-y-2">
                    <select
                      value={forma}
                      onChange={e => setForma(e.target.value)}
                      className="w-full bg-[#0f172a] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-500"
                    >
                      <option value="">-- Forma de cobro --</option>
                      <option value="transferencia">Transferencia</option>
                      <option value="efectivo">Efectivo</option>
                      <option value="mixto">Mixto</option>
                    </select>
                    <input
                      type="number"
                      value={monto}
                      onChange={e => setMonto(e.target.value)}
                      placeholder="Monto cobrado"
                      className="w-full bg-[#0f172a] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-500"
                    />
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => setEditForma(false)} className="px-3 py-2 text-sm text-gray-400 hover:text-white">✕</button>
                    <button
                      onClick={saveCobro}
                      disabled={saving}
                      className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm disabled:opacity-50"
                    >
                      {saving ? '...' : 'Guardar'}
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setEditForma(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600/20 hover:bg-green-600/30 border border-green-500/30 rounded-lg text-sm text-green-300 transition-colors"
                >
                  <Check size={14} /> Registrar cobro
                </button>
              )}
            </div>
          )}

          {/* Acciones */}
          <div className="flex justify-end">
            <button
              onClick={toggleCerrada}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                liq.cerrada
                  ? 'bg-white/5 hover:bg-white/10 text-gray-300 border border-gray-600'
                  : 'bg-amber-600/20 hover:bg-amber-600/30 border border-amber-500/30 text-amber-300'
              }`}
            >
              {liq.cerrada ? <><Unlock size={14} /> Reabrir</> : <><Lock size={14} /> Cerrar mes</>}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Página Principal ─────────────────────────────────────────────────────────

export default function Liquidaciones() {
  const [periodo, setPeriodo] = useState(getPeriodo())
  const [profesionales, setProfesionales] = useState([])
  const [liquidaciones, setLiquidaciones] = useState([])
  const [loading, setLoading] = useState(true)
  const [nuevaModal, setNuevaModal] = useState(null)  // profId

  async function fetchAll() {
    setLoading(true)
    try {
      const [resProf, resLiq] = await Promise.all([
        api.get('/profesionales/?activo=true'),
        api.get(`/profesionales/liquidaciones/periodo/${periodo}`),
      ])
      setProfesionales(resProf.data)
      setLiquidaciones(resLiq.data)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchAll() }, [periodo])

  const liqMap = Object.fromEntries(liquidaciones.map(l => [l.profesional_id, l]))

  const [year, month] = periodo.split('-')
  const periodoLabel = `${MONTHS[Number(month) - 1]} ${year}`

  const totalHonorarios = liquidaciones.reduce((s, l) => s + l.honorarios_totales, 0)
  const totalAdelantos = liquidaciones.reduce((s, l) => s + l.adelantos_percibidos, 0)
  const totalCobrar = liquidaciones.reduce((s, l) => s + l.total_a_cobrar, 0)

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Liquidaciones</h1>
          <p className="text-gray-400 text-sm mt-0.5">R-04 — Liquidación mensual de profesionales</p>
        </div>
        <input
          type="month"
          value={periodo}
          onChange={e => setPeriodo(e.target.value)}
          className="bg-[#1e293b] border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-violet-500"
        />
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total honorarios', value: formatARS(totalHonorarios), color: 'text-white' },
          { label: 'Adelantos percibidos', value: formatARS(totalAdelantos), color: 'text-red-400' },
          { label: 'Total a cobrar', value: formatARS(totalCobrar), color: 'text-violet-300' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-[#1e293b] rounded-xl border border-gray-700/40 px-5 py-4">
            <p className="text-xs text-gray-400">{label}</p>
            <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
            <p className="text-xs text-gray-500 mt-0.5">{periodoLabel}</p>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="text-center text-gray-400 py-20">Cargando...</div>
      ) : (
        <div className="space-y-4">
          {profesionales.map(prof => {
            const liq = liqMap[prof.id]
            if (liq) {
              return <LiquidacionCard key={prof.id} liq={liq} onRefresh={fetchAll} />
            }
            // Sin liquidación para este período
            return (
              <div key={prof.id} className="bg-[#1e293b] rounded-2xl border border-dashed border-gray-700/40 px-5 py-4 flex items-center justify-between">
                <div>
                  <p className="text-white font-medium">{prof.nombre} {prof.apellido || ''}</p>
                  <p className="text-xs text-gray-500 capitalize">{prof.tipo}</p>
                </div>
                <button
                  onClick={() => setNuevaModal(prof.id)}
                  className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 rounded-lg text-sm text-white font-medium transition-colors"
                >
                  <Plus size={14} /> Nueva liquidación
                </button>
              </div>
            )
          })}
          {profesionales.length === 0 && (
            <div className="text-center py-20">
              <p className="text-gray-400">Sin profesionales registrados.</p>
              <p className="text-gray-500 text-sm mt-1">Agregue profesionales desde el módulo correspondiente.</p>
            </div>
          )}
        </div>
      )}

      {nuevaModal && (
        <NuevaLiquidacionModal
          profId={nuevaModal}
          periodo={periodo}
          onClose={() => setNuevaModal(null)}
          onCreated={fetchAll}
        />
      )}
    </div>
  )
}
