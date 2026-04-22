import { useState, useRef } from 'react'
import { Upload, Download, FileSpreadsheet, CheckCircle, AlertTriangle, Loader2, X } from 'lucide-react'
import PageHeader from '../components/UI/PageHeader'
import api from '../utils/api'

export default function Herramientas() {
  const [archivo, setArchivo]       = useState(null)
  const [estado, setEstado]         = useState('idle')  // idle | procesando | listo | error
  const [stats, setStats]           = useState(null)
  const [errorMsg, setErrorMsg]     = useState('')
  const [urlDescarga, setUrlDescarga] = useState(null)
  const [nombreSalida, setNombreSalida] = useState('')
  const inputRef = useRef(null)

  const resetear = () => {
    setArchivo(null)
    setEstado('idle')
    setStats(null)
    setErrorMsg('')
    if (urlDescarga) URL.revokeObjectURL(urlDescarga)
    setUrlDescarga(null)
    setNombreSalida('')
    if (inputRef.current) inputRef.current.value = ''
  }

  const onSeleccionarArchivo = (e) => {
    const file = e.target.files[0]
    if (!file) return
    resetear()
    setArchivo(file)
    setEstado('idle')
  }

  const onDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (!file) return
    resetear()
    setArchivo(file)
  }

  const procesar = async () => {
    if (!archivo) return
    setEstado('procesando')
    setErrorMsg('')

    const form = new FormData()
    form.append('archivo', archivo)

    try {
      const res = await api.post('/herramientas/limpiar-libro-iva', form, {
        responseType: 'blob',
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      // Extraer nombre de archivo del header
      const disposition = res.headers['content-disposition'] || ''
      const match = disposition.match(/filename="(.+)"/)
      const nombre = match ? match[1] : archivo.name.replace('.xlsx', '_corregido.xlsx')

      const url = URL.createObjectURL(new Blob([res.data]))
      setUrlDescarga(url)
      setNombreSalida(nombre)

      // Leer stats del header si las enviamos, sino mostrar generico
      setStats({
        archivo: archivo.name,
        tamaño: (archivo.size / 1024).toFixed(1) + ' KB',
      })
      setEstado('listo')
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Error desconocido'
      setErrorMsg(typeof msg === 'string' ? msg : JSON.stringify(msg))
      setEstado('error')
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-2xl">
      <PageHeader
        title="Herramientas IVA"
        subtitle="Procesamiento de archivos — R-01 Limpieza Libro IVA"
      />

      {/* ── Zona de upload ── */}
      <div className="card space-y-4">
        <div className="flex items-center gap-2 mb-1">
          <FileSpreadsheet className="text-violet-400" size={20} />
          <h2 className="text-white font-semibold">Limpiar Libro IVA Compras</h2>
        </div>
        <p className="text-sm text-gray-400">
          Subí el Excel <span className="text-gray-300 font-mono">"Mis Comprobantes Recibidos"</span> exportado
          desde ARCA. El sistema corrige los comprobantes tipo B/C y el formato de tipo de cambio
          para que Holistor pueda importarlo sin errores.
        </p>

        {/* Drop zone */}
        <div
          onDragOver={e => e.preventDefault()}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={`
            border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors
            ${archivo
              ? 'border-violet-500/60 bg-violet-500/5'
              : 'border-gray-600 hover:border-violet-500/50 hover:bg-violet-500/5'
            }
          `}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".xlsx,.xls"
            className="hidden"
            onChange={onSeleccionarArchivo}
          />
          {archivo ? (
            <div className="flex items-center justify-center gap-3">
              <FileSpreadsheet className="text-violet-400" size={28} />
              <div className="text-left">
                <p className="text-white font-medium">{archivo.name}</p>
                <p className="text-gray-400 text-sm">{(archivo.size / 1024).toFixed(1)} KB</p>
              </div>
              <button
                onClick={e => { e.stopPropagation(); resetear() }}
                className="ml-4 text-gray-500 hover:text-gray-300"
              >
                <X size={16} />
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <Upload className="mx-auto text-gray-500" size={36} />
              <p className="text-gray-400 text-sm">
                Arrastrá el archivo acá o <span className="text-violet-400 underline">hacé clic para seleccionar</span>
              </p>
              <p className="text-gray-600 text-xs">Soporta .xlsx y .xls</p>
            </div>
          )}
        </div>

        {/* Botón procesar */}
        <button
          onClick={procesar}
          disabled={!archivo || estado === 'procesando'}
          className={`
            w-full flex items-center justify-center gap-2 py-3 rounded-lg font-semibold text-sm transition-colors
            ${!archivo || estado === 'procesando'
              ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
              : 'bg-violet-600 hover:bg-violet-500 text-white'
            }
          `}
        >
          {estado === 'procesando' ? (
            <><Loader2 className="animate-spin" size={18} /> Procesando...</>
          ) : (
            <><Upload size={18} /> Procesar archivo</>
          )}
        </button>
      </div>

      {/* ── Resultado OK ── */}
      {estado === 'listo' && (
        <div className="card border border-emerald-500/30 bg-emerald-500/5 space-y-4">
          <div className="flex items-center gap-2">
            <CheckCircle className="text-emerald-400" size={20} />
            <h3 className="text-emerald-400 font-semibold">Archivo procesado correctamente</h3>
          </div>
          {stats && (
            <div className="text-sm text-gray-400 space-y-1">
              <p>Archivo original: <span className="text-gray-200">{stats.archivo}</span></p>
              <p>Tamaño: <span className="text-gray-200">{stats.tamaño}</span></p>
            </div>
          )}
          <a
            href={urlDescarga}
            download={nombreSalida}
            className="flex items-center justify-center gap-2 w-full py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm transition-colors"
          >
            <Download size={18} />
            Descargar {nombreSalida}
          </a>
          <button onClick={resetear} className="w-full text-gray-500 hover:text-gray-300 text-sm py-1">
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
          <p className="text-sm text-gray-400">{errorMsg}</p>
          <button onClick={resetear} className="text-gray-500 hover:text-gray-300 text-sm">
            Intentar de nuevo
          </button>
        </div>
      )}
    </div>
  )
}
