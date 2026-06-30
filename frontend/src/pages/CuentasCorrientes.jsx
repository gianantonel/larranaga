import { useState, useEffect } from 'react'
import { getClients, getMovimientosCC, createMovimientoCC, getProfesionales, getCotizacionDolar } from '../utils/api'
import { Wallet, Plus, ArrowUpRight, ArrowDownRight, Search, ArrowRightLeft, Eye, EyeOff } from 'lucide-react'

const currentMonth = () => new Date().toISOString().slice(0, 7)  // YYYY-MM
const FORMAS_PAGO = ['efectivo', 'transferencia', 'cheque', 'deposito']

export default function CuentasCorrientes() {
  const [clients, setClients] = useState([])
  const [profesionales, setProfesionales] = useState([])
  const [selectedClient, setSelectedClient] = useState(null)
  const [movimientos, setMovimientos] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)

  // Form state
  const [tipo, setTipo] = useState('ingreso')
  const [monto, setMonto] = useState('')
  const [concepto, setConcepto] = useState('')
  const [fecha, setFecha] = useState(new Date().toISOString().split('T')[0])
  const [periodoHonorario, setPeriodoHonorario] = useState(currentMonth())
  const [formaPago, setFormaPago] = useState('efectivo')
  const [profesionalId, setProfesionalId] = useState('')
  const [notas, setNotas] = useState('')
  // Moneda / cotización (USD)
  const [moneda, setMoneda] = useState('ARS')
  const [cotizacion, setCotizacion] = useState('')
  const [showCotiz, setShowCotiz] = useState(false)
  const [cotizSugerida, setCotizSugerida] = useState(null)
  const [loadingCotiz, setLoadingCotiz] = useState(false)

  // El cobro cuenta como adelanto del profesional cuando es ingreso NO en efectivo
  const esAdelanto = tipo === 'ingreso' && formaPago !== 'efectivo'

  useEffect(() => {
    fetchClients()
    getProfesionales({ activo: true })
      .then(res => setProfesionales(res.data))
      .catch(err => console.error(err))
  }, [])

  const handleVerCotizacion = async () => {
    const next = !showCotiz
    setShowCotiz(next)
    if (next && !cotizSugerida) {
      try {
        setLoadingCotiz(true)
        const res = await getCotizacionDolar()
        setCotizSugerida(res.data?.disponible ? res.data : { disponible: false })
      } catch {
        setCotizSugerida({ disponible: false })
      } finally {
        setLoadingCotiz(false)
      }
    }
  }

  const fetchClients = async () => {
    try {
      setLoading(true)
      const res = await getClients()
      setClients(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectClient = async (client) => {
    setSelectedClient(client)
    try {
      const res = await getMovimientosCC(client.id)
      setMovimientos(res.data)
    } catch (err) {
      console.error(err)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!selectedClient) return

    if (moneda === 'USD' && !(parseFloat(cotizacion) > 0)) {
      alert('Ingresá la cotización (ARS por USD) para movimientos en dólares.')
      return
    }

    try {
      const data = {
        client_id: selectedClient.id,
        tipo,
        monto: parseFloat(monto),
        moneda,
        cotizacion: moneda === 'USD' ? parseFloat(cotizacion) : null,
        concepto,
        fecha,
        periodo_honorario: periodoHonorario || null,
        forma_pago: formaPago,
        // El adelanto al profesional solo aplica en ingreso no-efectivo
        profesional_id: esAdelanto && profesionalId ? parseInt(profesionalId) : null,
        notas
      }
      await createMovimientoCC(data)
      // Refresh movements and clients (to update balance)
      handleSelectClient(selectedClient)
      fetchClients()
      setIsModalOpen(false)
      // Reset form
      setMonto('')
      setConcepto('')
      setNotas('')
      setFormaPago('efectivo')
      setProfesionalId('')
      setPeriodoHonorario(currentMonth())
      setMoneda('ARS')
      setCotizacion('')
      setShowCotiz(false)
    } catch (err) {
      console.error(err)
      alert("Error al guardar el movimiento")
    }
  }

  const filteredClients = clients.filter(c => 
    c.name.toLowerCase().includes(search.toLowerCase()) || 
    (c.cuit && c.cuit.includes(search))
  )

  return (
    <div className="page">
      <header className="flex justify-between items-center">
        <div className="min-w-0">
          <h1 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
            <Wallet className="text-violet-500" />
            Cuentas Corrientes
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Gestiona los saldos, ingresos y egresos de los clientes
          </p>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Left Column: Client List */}
        <div className="bg-[#1e293b] rounded-xl border border-gray-700/50 flex flex-col h-[calc(100vh-12rem)]">
          <div className="p-4 border-b border-gray-700/50">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                placeholder="Buscar cliente..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-[#0f172a] border border-gray-700 rounded-lg py-2 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-violet-500"
              />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {loading ? (
              <p className="text-center text-gray-500 py-4">Cargando...</p>
            ) : filteredClients.map(client => (
              <button
                key={client.id}
                onClick={() => handleSelectClient(client)}
                className={`w-full text-left p-3 rounded-lg transition-colors flex justify-between items-center ${
                  selectedClient?.id === client.id ? 'bg-violet-600/20 border border-violet-500/50' : 'hover:bg-white/5 border border-transparent'
                }`}
              >
                <div className="overflow-hidden">
                  <p className="text-sm font-medium text-white truncate">{client.name}</p>
                  <p className="text-xs text-gray-400 truncate">{client.cuit || 'Sin CUIT'}</p>
                </div>
                <div className={`text-sm font-semibold whitespace-nowrap ml-3 ${
                  (client.saldo_cc || 0) > 0 ? 'text-emerald-400' : (client.saldo_cc || 0) < 0 ? 'text-rose-400' : 'text-gray-400'
                }`}>
                  ${Math.abs(client.saldo_cc || 0).toLocaleString('es-AR')}
                  {(client.saldo_cc || 0) < 0 && ' (Deuda)'}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Right Column: Details & Movements */}
        <div className="lg:col-span-2 bg-[#1e293b] rounded-xl border border-gray-700/50 flex flex-col h-[calc(100vh-12rem)]">
          {selectedClient ? (
            <>
              <div className="p-6 border-b border-gray-700/50 flex justify-between items-start">
                <div>
                  <h2 className="text-xl font-bold text-white">{selectedClient.name}</h2>
                  <p className="text-gray-400 text-sm">CUIT: {selectedClient.cuit || 'N/A'}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-400 mb-1">Saldo Actual</p>
                  <p className={`text-2xl font-bold ${
                    (selectedClient.saldo_cc || 0) > 0 ? 'text-emerald-400' : (selectedClient.saldo_cc || 0) < 0 ? 'text-rose-400' : 'text-gray-300'
                  }`}>
                    ${Math.abs(selectedClient.saldo_cc || 0).toLocaleString('es-AR')}
                    <span className="text-sm ml-1">
                      {(selectedClient.saldo_cc || 0) < 0 ? 'Deuda' : (selectedClient.saldo_cc || 0) > 0 ? 'A favor' : ''}
                    </span>
                  </p>
                </div>
              </div>

              <div className="p-4 border-b border-gray-700/50 bg-white/[0.02] flex justify-between items-center">
                <h3 className="text-white font-medium">Historial de Movimientos</h3>
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
                >
                  <Plus size={16} />
                  Nuevo Movimiento
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-4">
                {movimientos.length === 0 ? (
                  <div className="text-center text-gray-500 py-10">
                    <Wallet size={48} className="mx-auto mb-3 opacity-20" />
                    <p>No hay movimientos registrados</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {movimientos.map(mov => (
                      <div key={mov.id} className="bg-[#0f172a] border border-gray-700/50 rounded-lg p-4 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            mov.tipo === 'ingreso' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-rose-500/10 text-rose-500'
                          }`}>
                            {mov.tipo === 'ingreso' ? <ArrowUpRight size={20} /> : <ArrowDownRight size={20} />}
                          </div>
                          <div>
                            <p className="text-white font-medium">{mov.concepto}</p>
                            <p className="text-xs text-gray-400">
                              {new Date(mov.fecha + 'T00:00:00').toLocaleDateString('es-AR')}
                              {mov.periodo_honorario && ` · cobra ${mov.periodo_honorario}`}
                              {mov.forma_pago && ` · ${mov.forma_pago}`}
                              {mov.moneda === 'USD' && mov.cotizacion && ` · TC $${mov.cotizacion.toLocaleString('es-AR')}`}
                            </p>
                            {mov.profesional_nombre && mov.forma_pago && mov.forma_pago !== 'efectivo' && mov.tipo === 'ingreso' && (
                              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-violet-300 bg-violet-500/10 border border-violet-500/30 rounded px-1.5 py-0.5 mt-1">
                                <ArrowRightLeft size={11} />
                                Adelanto → {mov.profesional_nombre}
                              </span>
                            )}
                            {mov.notas && <p className="text-xs text-gray-500 mt-1">{mov.notas}</p>}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className={`font-bold ${mov.tipo === 'ingreso' ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {mov.tipo === 'ingreso' ? '+' : '-'}{mov.moneda === 'USD' ? 'US$' : '$'}{mov.monto.toLocaleString('es-AR')}
                          </div>
                          {mov.moneda === 'USD' && mov.cotizacion && (
                            <div className="text-[11px] text-gray-500">
                              ≈ ${(mov.monto * mov.cotizacion).toLocaleString('es-AR')} ARS
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
              <Wallet size={64} className="mb-4 opacity-20" />
              <p>Selecciona un cliente para ver su cuenta corriente</p>
            </div>
          )}
        </div>
      </div>

      {/* Modal Nuevo Movimiento */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-[#1e293b] rounded-2xl w-full max-w-md border border-gray-700 shadow-2xl overflow-hidden">
            <div className="p-6 border-b border-gray-700">
              <h2 className="text-xl font-bold text-white">Registrar Movimiento</h2>
              <p className="text-sm text-gray-400 mt-1">Para {selectedClient?.name}</p>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setTipo('ingreso')}
                  className={`py-2 rounded-lg font-medium text-sm border transition-colors ${
                    tipo === 'ingreso' 
                      ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400' 
                      : 'bg-transparent border-gray-600 text-gray-400 hover:bg-white/5'
                  }`}
                >
                  Ingreso / Cobro
                </button>
                <button
                  type="button"
                  onClick={() => setTipo('egreso')}
                  className={`py-2 rounded-lg font-medium text-sm border transition-colors ${
                    tipo === 'egreso' 
                      ? 'bg-rose-500/20 border-rose-500 text-rose-400' 
                      : 'bg-transparent border-gray-600 text-gray-400 hover:bg-white/5'
                  }`}
                >
                  Egreso / Cargo
                </button>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs font-medium text-gray-400 mb-1">
                    Monto ({moneda === 'USD' ? 'US$' : '$'})
                  </label>
                  <input
                    type="number"
                    required
                    step="0.01"
                    min="0.01"
                    value={monto}
                    onChange={(e) => setMonto(e.target.value)}
                    className="w-full bg-[#0f172a] border border-gray-700 rounded-lg py-2 px-3 text-white focus:outline-none focus:border-violet-500"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Moneda</label>
                  <div className="grid grid-cols-2 gap-1">
                    {['ARS', 'USD'].map(m => (
                      <button
                        key={m}
                        type="button"
                        onClick={() => { setMoneda(m); if (m === 'ARS') { setCotizacion(''); setShowCotiz(false) } else { setShowCotiz(true); handleVerCotizacion() } }}
                        className={`py-2 rounded-lg font-medium text-xs border transition-colors ${
                          moneda === m
                            ? 'bg-violet-500/20 border-violet-500 text-violet-300'
                            : 'bg-transparent border-gray-600 text-gray-400 hover:bg-white/5'
                        }`}
                      >
                        {m}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {moneda === 'USD' && (
                <div>
                  <label className="flex items-center justify-between text-xs font-medium text-gray-400 mb-1">
                    <span>Cotización (ARS por US$)</span>
                    <button
                      type="button"
                      onClick={handleVerCotizacion}
                      className="flex items-center gap-1 text-violet-300 hover:text-violet-200"
                      title="Ver cotización sugerida (dólar oficial)"
                    >
                      {showCotiz ? <EyeOff size={14} /> : <Eye size={14} />}
                      {showCotiz ? 'Ocultar sugerida' : 'Ver sugerida'}
                    </button>
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={cotizacion}
                    onChange={(e) => setCotizacion(e.target.value)}
                    className="w-full bg-[#0f172a] border border-gray-700 rounded-lg py-2 px-3 text-white focus:outline-none focus:border-violet-500"
                    placeholder="Ej. 1180.50"
                  />
                  {showCotiz && (
                    <div className="mt-2 text-xs bg-[#0f172a] border border-gray-700/60 rounded-lg p-2">
                      {loadingCotiz ? (
                        <span className="text-gray-400">Consultando dólar oficial…</span>
                      ) : cotizSugerida?.disponible ? (
                        <div className="flex items-center justify-between">
                          <span className="text-gray-300">
                            {cotizSugerida.fuente}: compra ${cotizSugerida.compra} · venta ${cotizSugerida.venta}
                          </span>
                          <button
                            type="button"
                            onClick={() => setCotizacion(String(cotizSugerida.sugerida))}
                            className="ml-2 px-2 py-1 rounded bg-violet-600 hover:bg-violet-700 text-white whitespace-nowrap"
                          >
                            Usar ${cotizSugerida.sugerida}
                          </button>
                        </div>
                      ) : (
                        <span className="text-amber-400">No se pudo traer la cotización. Cargala manualmente.</span>
                      )}
                    </div>
                  )}
                  {monto && parseFloat(cotizacion) > 0 && (
                    <p className="text-xs text-gray-500 mt-1">
                      ≈ ${(parseFloat(monto) * parseFloat(cotizacion)).toLocaleString('es-AR')} ARS
                    </p>
                  )}
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Concepto</label>
                <input
                  type="text"
                  required
                  value={concepto}
                  onChange={(e) => setConcepto(e.target.value)}
                  className="w-full bg-[#0f172a] border border-gray-700 rounded-lg py-2 px-3 text-white focus:outline-none focus:border-violet-500"
                  placeholder="Ej. Honorarios Marzo, Pago transferencia..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Fecha</label>
                  <input
                    type="date"
                    required
                    value={fecha}
                    onChange={(e) => setFecha(e.target.value)}
                    className="w-full bg-[#0f172a] border border-gray-700 rounded-lg py-2 px-3 text-white focus:outline-none focus:border-violet-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">Mes que se cobra</label>
                  <input
                    type="month"
                    value={periodoHonorario}
                    onChange={(e) => setPeriodoHonorario(e.target.value)}
                    className="w-full bg-[#0f172a] border border-gray-700 rounded-lg py-2 px-3 text-white focus:outline-none focus:border-violet-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Forma de pago</label>
                <div className="grid grid-cols-2 gap-3">
                  {FORMAS_PAGO.map(fp => (
                    <button
                      key={fp}
                      type="button"
                      onClick={() => setFormaPago(fp)}
                      className={`py-2 rounded-lg font-medium text-sm border capitalize transition-colors ${
                        formaPago === fp
                          ? 'bg-violet-500/20 border-violet-500 text-violet-300'
                          : 'bg-transparent border-gray-600 text-gray-400 hover:bg-white/5'
                      }`}
                    >
                      {fp}
                    </button>
                  ))}
                </div>
              </div>

              {esAdelanto && (
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">
                    Profesional que recibió el pago
                  </label>
                  <select
                    value={profesionalId}
                    onChange={(e) => setProfesionalId(e.target.value)}
                    className="w-full bg-[#0f172a] border border-gray-700 rounded-lg py-2 px-3 text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="">— Ninguno —</option>
                    {profesionales.map(p => (
                      <option key={p.id} value={p.id}>{p.nombre}</option>
                    ))}
                  </select>
                  {profesionalId && (
                    <p className="text-xs text-violet-300/80 mt-1 flex items-center gap-1">
                      <ArrowRightLeft size={12} />
                      Se computa como adelanto de honorarios del profesional en {periodoHonorario || 'el mes seleccionado'}.
                    </p>
                  )}
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Notas (Opcional)</label>
                <textarea
                  value={notas}
                  onChange={(e) => setNotas(e.target.value)}
                  className="w-full bg-[#0f172a] border border-gray-700 rounded-lg py-2 px-3 text-white focus:outline-none focus:border-violet-500 h-20 resize-none"
                  placeholder="Detalles adicionales..."
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 py-2 px-4 rounded-lg font-medium text-sm text-gray-300 bg-white/5 hover:bg-white/10 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 px-4 rounded-lg font-medium text-sm text-white bg-violet-600 hover:bg-violet-700 transition-colors"
                >
                  Guardar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
