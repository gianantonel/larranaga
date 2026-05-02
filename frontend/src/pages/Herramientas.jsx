import { useState, useRef, useEffect } from 'react'
import {
  Upload, Download, FileSpreadsheet, CheckCircle,
  AlertTriangle, Loader2, X, History, User, FileDown
} from 'lucide-react'
import PageHeader from '../components/UI/PageHeader'
import api, { generarHwcrarca } from '../utils/api'
import { formatDate } from '../utils/helpers'

export default function Herramientas() {
  const [clientes, setClientes]       = useState([])
  const [clienteId, setClienteId]     = useState('')
  const [archivo, setArchivo]         = useState(null)
  const [estado, setEstado]           = useState('idle')  // idle | procesando | listo | error
  const [resultado, setResultado]     = useState(null)
  const [errorMsg, setErrorMsg]       = useState('')
  const [historial, setHistorial]     = useState([])
  const [loadingHist, setLoadingHist] = useState(false)
  const [hwcrarcaState, setHwcrarcaState] = useState({ id: null, loading: false, stats: null, error: null })
  const inputRef = useRef(null)

  // Cargar clientes al montar
  useEffect(() => {
    api.get('/clients/').then(r => setClientes(r.data)).catch(() => {})
  }, [])

  // Cargar historial cuando cambia el cliente o se procesa uno nuevo
  useEffect(() => {
    if (!clienteId) { setHistorial([]); return }
    setLoadingHist(true)
    api.get('/herramientas/limpiar-libro-iva/historial', { params: { client_id: clienteId } })
      .then(r => setHistorial(r.data))
      .catch(() => setHistorial([]))
      .finally(() => setLoadingHist(false))
  }, [clienteId, resultado])

  const limpiarEstado = () => {
    setEstado('idle')
    setResultado(null)
    setErrorMsg('')
  }

  const quitarArchivo = () => {
    setArchivo(null)
    limpiarEstado()
    if (inputRef.current) inputRef.current.value = ''
  }

  // Captura el File ANTES de tocar cualquier estado
  const onSeleccionar = (e) => {
    const file = e.target.files[0]
    if (!file) return
    limpiarEstado()
    setArchivo(file)
  }

  const onDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (!file) return
    limpiarEstado()
    setArchivo(file)
  }

  const abrirSelector = () => inputRef.current?.click()

  const procesar = async () => {
    if (!archivo || !clienteId) return
    setEstado('procesando')
    setErrorMsg('')

    const form = new FormData()
    form.append('client_id', clienteId)
    form.append('archivo', archivo)

    try {
      const res = await api.post('/herramientas/limpiar-libro-iva', form, {
        headers: { 'Content-Type': undefined },
      })
      setResultado(res.data)
      setEstado('listo')
    } catch (err) {
      let msg = err.message || 'Error desconocido'
      if (err.response?.data instanceof Blob) {
        try { msg = JSON.stringify(JSON.parse(await err.response.data.text()), null, 2) } catch {}
      } else {
        msg = err.response?.data?.detail || msg
      }
      setErrorMsg(typeof msg === 'string' ? msg : JSON.stringify(msg))
      setEstado('error')
    }
  }

  const descargar = (id, nombre) => {
    api.get(`/herramientas/limpiar-libro-iva/${id}/descargar`, { responseType: 'blob' })
      .then(r => {
        const url = URL.createObjectURL(new Blob([r.data]))
        const a   = document.createElement('a')
        a.href = url; a.download = nombre; a.click()
        URL.revokeObjectURL(url)
      })
  }

  // R-10 — Genera HWCRARCA y descarga; lee stats de los response headers
  const descargarHwcrarcaFn = async (id, nombreOriginal) => {
    setHwcrarcaState({ id, loading: true, stats: null, error: null })
    try {
      const r = await generarHwcrarca(id)
      // Stats vienen en headers
      const stats = {
        totalFilas:  Number(r.headers['x-total-filas']  ?? 0),
        filasBC:     Number(r.headers['x-filas-b-c']    ?? 0),
        filasCF:     Number(r.headers['x-filas-cf']     ?? 0),
        filasAdv:    Number(r.headers['x-filas-adv']    ?? 0),
        cuadreOk:    r.headers['x-cuadre-ok'] === 'true',
      }
      // Trigger download
      const stem = nombreOriginal.replace(/\.[^/.]+$/, '')
      const filename = `HWCRARCA_${stem}.xlsx`
      const url = URL.createObjectURL(new Blob([r.data]))
      const a   = document.createElement('a')
      a.href = url; a.download = filename; a.click()
      URL.revokeObjectURL(url)
      setHwcrarcaState({ id, loading: false, stats, error: null })
    } catch (err) {
      let msg = 'Error al generar HWCRARCA'
      if (err.response?.data instanceof Blob) {
        try { msg = JSON.parse(await err.response.data.text()).detail ?? msg } catch {}
      } else {
        msg = err.response?.data?.detail || err.message || msg
      }
      setHwcrarcaState({ id, loading: false, stats: null, error: msg })
    }
  }

  const puedeProcessar = archivo && clienteId && estado !== 'procesando'

  return (
    <div className="p-6 space-y-6 max-w-3xl">
      <PageHeader
        title="Herramientas IVA"
        subtitle="Procesamiento de archivos — R-01 Limpieza Libro IVA + R-02 División por alícuotas"
      />

      {/* ── Formulario ── */}
      <div className="card space-y-4">
        <div className="flex items-center gap-2 mb-1">
          <FileSpreadsheet className="text-violet-400" size={20} />
          <h2 className="text-white font-semibold">Limpiar Libro IVA Compras</h2>
        </div>
        <p className="text-sm text-gray-400">
          Seleccioná el cliente, subí el Excel{' '}
          <span className="text-gray-300 font-mono">"Mis Comprobantes Recibidos"</span>{' '}
          exportado desde ARCA y descargá el archivo corregido listo para Holistor.
        </p>

        {/* Selector de cliente */}
        <div className="space-y-1">
          <span className="text-xs text-gray-400 uppercase tracking-wide">Cliente</span>
          <div className="relative">
            <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <select
              value={clienteId}
              onChange={e => { setClienteId(e.target.value); quitarArchivo() }}
              className="input-field pl-9 w-full"
            >
              <option value="">Seleccioná un cliente...</option>
              {clientes.map(c => (
                <option key={c.id} value={c.id}>{c.name} — {c.cuit}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Input de archivo — oculto, activado por onClick del drop zone */}
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx,.xls"
          className="hidden"
          onChange={onSeleccionar}
        />

        {/* Drop zone */}
        <div
          onDragOver={e => e.preventDefault()}
          onDrop={onDrop}
          onClick={abrirSelector}
          className={`
            border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors
            ${archivo
              ? 'border-violet-500/60 bg-violet-500/5'
              : 'border-gray-600 hover:border-violet-500/50 hover:bg-violet-500/5'
            }
          `}
        >
          {archivo ? (
            <div className="flex items-center justify-center gap-3">
              <FileSpreadsheet className="text-violet-400" size={28} />
              <div className="text-left">
                <p className="text-white font-medium">{archivo.name}</p>
                <p className="text-gray-400 text-sm">{(archivo.size / 1024).toFixed(1)} KB</p>
              </div>
              <button
                type="button"
                onClick={e => { e.stopPropagation(); quitarArchivo() }}
                className="ml-4 text-gray-500 hover:text-gray-300"
              >
                <X size={16} />
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <Upload className="mx-auto text-gray-500" size={36} />
              <p className="text-gray-400 text-sm">
                Arrastrá el archivo acá o{' '}
                <span className="text-violet-400 underline">hacé clic para seleccionar</span>
              </p>
              <p className="text-gray-600 text-xs">Soporta .xlsx y .xls</p>
            </div>
          )}
        </div>

        {/* Botón procesar */}
        <button
          onClick={procesar}
          disabled={!puedeProcessar}
          className={`w-full flex items-center justify-center gap-2 py-3 rounded-lg font-semibold text-sm transition-colors
            ${puedeProcessar
              ? 'bg-violet-600 hover:bg-violet-500 text-white'
              : 'bg-gray-700 text-gray-500 cursor-not-allowed'
            }`}
        >
          {estado === 'procesando'
            ? <><Loader2 className="animate-spin" size={18} /> Procesando...</>
            : <><Upload size={18} /> Procesar archivo</>}
        </button>
      </div>

      {/* ── Resultado OK ── */}
      {estado === 'listo' && resultado && (
        <div className="card border border-emerald-500/30 bg-emerald-500/5 space-y-4">
          <div className="flex items-center gap-2">
            <CheckCircle className="text-emerald-400" size={20} />
            <h3 className="text-emerald-400 font-semibold">Archivo procesado correctamente</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
            <div className="bg-white/5 rounded-lg py-3">
              <p className="text-2xl font-bold text-white">{resultado.total_filas}</p>
              <p className="text-xs text-gray-400 mt-0.5">Comprobantes</p>
            </div>
            <div className="bg-white/5 rounded-lg py-3">
              <p className="text-2xl font-bold text-emerald-400">{resultado.filas_bc_corregidas}</p>
              <p className="text-xs text-gray-400 mt-0.5">B/C corregidos</p>
            </div>
            <div className="bg-white/5 rounded-lg py-3">
              <p className="text-2xl font-bold text-amber-400">{resultado.filas_multi_alicuota ?? 0}</p>
              <p className="text-xs text-gray-400 mt-0.5">Multi-alícuota divididas</p>
            </div>
            <div className="bg-white/5 rounded-lg py-3">
              <p className="text-2xl font-bold text-violet-400">{resultado.filas_salida ?? resultado.total_filas}</p>
              <p className="text-xs text-gray-400 mt-0.5">Filas salida</p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              onClick={() => descargar(resultado.id, resultado.nombre_corregido)}
              className="flex items-center justify-center gap-2 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm transition-colors"
            >
              <Download size={18} />
              Excel limpio
            </button>
            <button
              onClick={() => descargarHwcrarcaFn(resultado.id, resultado.nombre_original)}
              disabled={hwcrarcaState.loading && hwcrarcaState.id === resultado.id}
              className="flex items-center justify-center gap-2 py-3 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white font-semibold text-sm transition-colors"
              title="Genera el archivo HWCRARCA listo para importar a Holistor"
            >
              {hwcrarcaState.loading && hwcrarcaState.id === resultado.id
                ? <><Loader2 className="animate-spin" size={18} /> Generando...</>
                : <><FileDown size={18} /> Generar HWCRARCA</>}
            </button>
          </div>

          {/* Stats HWCRARCA después de generar */}
          {hwcrarcaState.id === resultado.id && hwcrarcaState.stats && (
            <div className="bg-violet-500/5 border border-violet-500/30 rounded-lg p-3 space-y-2">
              <p className="text-violet-300 text-sm font-semibold flex items-center gap-2">
                <CheckCircle size={14} /> HWCRARCA generado y descargado
              </p>
              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div className="bg-white/5 rounded py-2">
                  <p className="font-bold text-white">{hwcrarcaState.stats.totalFilas}</p>
                  <p className="text-gray-400">Filas</p>
                </div>
                <div className="bg-white/5 rounded py-2">
                  <p className="font-bold text-amber-400">{hwcrarcaState.stats.filasBC}</p>
                  <p className="text-gray-400">Tipo B/C</p>
                </div>
                <div className="bg-white/5 rounded py-2">
                  <p className="font-bold text-blue-400">{hwcrarcaState.stats.filasCF}</p>
                  <p className="text-gray-400">Cons. final</p>
                </div>
                <div className={`rounded py-2 ${hwcrarcaState.stats.cuadreOk ? 'bg-emerald-500/10' : 'bg-rose-500/10'}`}>
                  <p className={`font-bold ${hwcrarcaState.stats.cuadreOk ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {hwcrarcaState.stats.cuadreOk ? '✓' : '✗'}
                  </p>
                  <p className="text-gray-400">Cuadre</p>
                </div>
              </div>
              {hwcrarcaState.stats.filasAdv > 0 && (
                <p className="text-xs text-amber-400/80">
                  ⚠ {hwcrarcaState.stats.filasAdv} fila{hwcrarcaState.stats.filasAdv !== 1 ? 's' : ''} con advertencia de cuadre (probablemente percepciones no expuestas en ARCA — no bloquea importación).
                </p>
              )}
              <p className="text-xs text-gray-500 leading-relaxed">
                Próximo paso: abrir el archivo descargado, guardar como <code className="text-violet-300">.prn</code> (Texto delimitado por espacios), e importar en Holistor: <em>Útiles → Importar Datos de otros sistemas → Compras</em>.
              </p>
            </div>
          )}

          {hwcrarcaState.id === resultado.id && hwcrarcaState.error && (
            <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-3 text-sm text-rose-300">
              <AlertTriangle className="inline mr-1.5" size={14} />
              {hwcrarcaState.error}
            </div>
          )}

          <button onClick={quitarArchivo} className="w-full text-gray-500 hover:text-gray-300 text-sm py-1">
            Procesar otro archivo
          </button>
        </div>
      )}

      {/* ── Error ── */}
      {estado === 'error' && (
        <div className="card border border-rose-500/30 bg-rose-500/5 space-y-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="text-rose-400" size={20} />
            <h3 className="text-rose-400 font-semibold">Error al procesar</h3>
          </div>
          <pre className="text-sm text-gray-400 whitespace-pre-wrap">{errorMsg}</pre>
          <button onClick={quitarArchivo} className="text-gray-500 hover:text-gray-300 text-sm">
            Intentar de nuevo
          </button>
        </div>
      )}

      {/* ── Historial ── */}
      {clienteId && (
        <div className="card space-y-3">
          <div className="flex items-center gap-2">
            <History className="text-gray-400" size={18} />
            <h3 className="text-white font-semibold">Historial del cliente</h3>
            {loadingHist && <Loader2 className="animate-spin text-gray-500" size={14} />}
          </div>

          {historial.length === 0 && !loadingHist ? (
            <p className="text-gray-500 text-sm">No hay archivos procesados para este cliente.</p>
          ) : (
            <div className="divide-y divide-gray-700/50">
              {historial.map(h => (
                <div key={h.id} className="flex items-center justify-between py-3 gap-3">
                  <div className="space-y-0.5 min-w-0 flex-1">
                    <p className="text-sm text-white font-medium truncate">{h.nombre_original}</p>
                    <p className="text-xs text-gray-500">
                      {formatDate(h.created_at)} · por {h.user_name} · {h.total_filas} filas · {h.filas_bc_corregidas} B/C corregidas
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => descargar(h.id, h.nombre_corregido)}
                      className="flex items-center gap-1.5 text-xs text-emerald-400 hover:text-emerald-300 transition-colors px-3 py-1.5 border border-emerald-500/30 rounded-lg"
                      title="Descargar Excel limpio (post R-01/R-02)"
                    >
                      <Download size={13} />
                      Excel
                    </button>
                    <button
                      onClick={() => descargarHwcrarcaFn(h.id, h.nombre_original)}
                      disabled={hwcrarcaState.loading && hwcrarcaState.id === h.id}
                      className="flex items-center gap-1.5 text-xs text-violet-400 hover:text-violet-300 transition-colors px-3 py-1.5 border border-violet-500/30 rounded-lg disabled:opacity-50"
                      title="Generar y descargar HWCRARCA listo para Holistor"
                    >
                      {hwcrarcaState.loading && hwcrarcaState.id === h.id
                        ? <Loader2 className="animate-spin" size={13} />
                        : <FileDown size={13} />}
                      HWCRARCA
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
