import { useState, useEffect } from 'react'
import { getClients, getMovimientosCC, createMovimientoCC } from '../utils/api'
import { Wallet, Plus, ArrowUpRight, ArrowDownRight, Search, X } from 'lucide-react'

export default function CuentasCorrientes() {
  const [clients, setClients] = useState([])
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
  const [notas, setNotas] = useState('')

  useEffect(() => {
    fetchClients()
  }, [])

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

  useEffect(() => {
    if (!isModalOpen) return
    const handleEsc = e => { if (e.key === 'Escape') setIsModalOpen(false) }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [isModalOpen])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!selectedClient) return

    try {
      const data = {
        client_id: selectedClient.id,
        tipo,
        monto: parseFloat(monto),
        concepto,
        fecha,
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
    <div className="p-6 space-y-6">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Wallet className="text-violet-500" />
            Cuentas Corrientes
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Gestiona los saldos, ingresos y egresos de los clientes
          </p>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Client List */}
        <div className="bg-[#1e293b] rounded-xl border border-gray-700/50 flex flex-col h-[400px] lg:h-[calc(100vh-12rem)]">
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
        <div className="lg:col-span-2 bg-[#1e293b] rounded-xl border border-gray-700/50 flex flex-col min-h-[500px] lg:h-[calc(100vh-12rem)]">
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
                            <p className="text-xs text-gray-400">{new Date(mov.fecha + 'T00:00:00').toLocaleDateString('es-AR')}</p>
                            {mov.notas && <p className="text-xs text-gray-500 mt-1">{mov.notas}</p>}
                          </div>
                        </div>
                        <div className={`font-bold ${mov.tipo === 'ingreso' ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {mov.tipo === 'ingreso' ? '+' : '-'}${mov.monto.toLocaleString('es-AR')}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-500 py-12 lg:py-0">
              <Wallet size={64} className="mb-4 opacity-20" />
              <p>Seleccioná un cliente para ver su cuenta corriente</p>
            </div>
          )}
        </div>
      </div>

      {/* Modal Nuevo Movimiento */}
      {isModalOpen && (
        <div className="modal-backdrop" onClick={() => setIsModalOpen(false)}>
          <div className="modal-panel max-w-md overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-gray-700/60 flex items-start justify-between">
              <div>
                <h2 className="text-xl font-bold text-white">Registrar Movimiento</h2>
                <p className="text-sm text-gray-400 mt-1">Para {selectedClient?.name}</p>
              </div>
              <button type="button" onClick={() => setIsModalOpen(false)} className="btn-icon mt-0.5"><X size={18} /></button>
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

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Monto ($)</label>
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
