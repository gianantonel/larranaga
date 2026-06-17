import { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown, Minus, AlertCircle, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react'
import { getPosicionIva } from '../utils/api'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import { formatCurrency } from '../utils/helpers'

// Devuelve el período AAAA-MM del mes actual
const periodoActual = () => {
  const hoy = new Date()
  const anio = hoy.getFullYear()
  const mes = String(hoy.getMonth() + 1).padStart(2, '0')
  return `${anio}-${mes}`
}

export default function PosicionIVA() {
  const [periodo, setPeriodo] = useState(periodoActual())
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [detalleAbierto, setDetalleAbierto] = useState(false)

  const cargar = (p) => {
    setLoading(true)
    setError(null)
    getPosicionIva(p)
      .then((res) => setData(res.data))
      .catch(() => setError('No se pudo obtener la posición IVA para el período seleccionado.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { cargar(periodo) }, [periodo])

  const handlePeriodo = (e) => setPeriodo(e.target.value)

  // Configuración visual según tipo de posición — dark theme
  const config = {
    deuda: {
      color: 'text-rose-400',
      bg: 'bg-rose-500/10 border-rose-500/30',
      badge: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
      icon: <TrendingUp className="w-8 h-8 text-rose-400" />,
      label: 'Deuda con AFIP',
    },
    a_favor: {
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/30',
      badge: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
      icon: <TrendingDown className="w-8 h-8 text-emerald-400" />,
      label: 'Saldo a favor',
    },
    neutro: {
      color: 'text-gray-300',
      bg: 'bg-gray-500/10 border-gray-500/30',
      badge: 'bg-gray-500/15 text-gray-300 border-gray-500/30',
      icon: <Minus className="w-8 h-8 text-gray-400" />,
      label: 'Posición neutra',
    },
    sin_datos: {
      color: 'text-gray-500',
      bg: 'bg-gray-800/30 border-gray-700/40',
      badge: 'bg-gray-700/40 text-gray-400 border-gray-700/40',
      icon: <AlertCircle className="w-8 h-8 text-gray-500" />,
      label: 'Sin datos',
    },
  }

  const tipo = data?.tipo ?? 'sin_datos'
  const cfg = config[tipo] ?? config.sin_datos

  const periodoLegible = (p) => {
    if (!p) return ''
    const [anio, mes] = p.split('-')
    const fecha = new Date(Number(anio), Number(mes) - 1, 1)
    return fecha.toLocaleDateString('es-AR', { month: 'long', year: 'numeric' })
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Posición IVA"
        subtitle="Resumen de débito y crédito fiscal del estudio por período"
      />

      {/* Selector de período */}
      <div className="card p-4 flex items-center gap-4">
        <label className="text-sm font-medium text-gray-300 whitespace-nowrap">Período:</label>
        <input
          type="month"
          value={periodo}
          onChange={handlePeriodo}
          className="input-field w-44 font-mono"
        />
        <span className="text-sm text-gray-500 capitalize">{periodoLegible(periodo)}</span>
      </div>

      {loading && (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      )}

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-center gap-3 text-rose-300 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          {error}
        </div>
      )}

      {data && !loading && (
        <>
          {/* Tarjetas principales */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Débito fiscal */}
            <div className="card">
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">
                IVA Débito Fiscal
              </p>
              <p className="text-2xl font-bold text-white">
                {formatCurrency(data.debito_fiscal)}
              </p>
              <p className="text-xs text-gray-500 mt-1">IVA generado por ventas</p>
            </div>

            {/* Crédito fiscal */}
            <div className="card">
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">
                IVA Crédito Fiscal
              </p>
              <p className="text-2xl font-bold text-white">
                {formatCurrency(data.credito_fiscal)}
              </p>
              <p className="text-xs text-gray-500 mt-1">IVA deducible por compras</p>
            </div>

            {/* Posición del mes */}
            <div className={`rounded-xl border p-6 ${cfg.bg}`}>
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Posición del Mes
                </p>
                {cfg.icon}
              </div>
              <p className={`text-2xl font-bold ${cfg.color}`}>
                {formatCurrency(Math.abs(data.posicion))}
              </p>
              <span className={`inline-block mt-2 text-xs font-semibold px-2 py-0.5 rounded-full border ${cfg.badge}`}>
                {cfg.label}
              </span>
            </div>
          </div>

          {/* Detalle por cliente (colapsable) */}
          {data.clientes_incluidos > 0 && (
            <div className="card p-0 overflow-hidden">
              <button
                className="w-full flex items-center justify-between px-5 py-4 text-sm font-medium text-gray-200 hover:bg-white/5 transition-colors"
                onClick={() => setDetalleAbierto(!detalleAbierto)}
              >
                <span>
                  Detalle por cliente —{' '}
                  <span className="text-gray-500">{data.clientes_incluidos} clientes incluidos</span>
                </span>
                {detalleAbierto ? (
                  <ChevronUp className="w-4 h-4 text-gray-400" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                )}
              </button>

              {detalleAbierto && (
                <div className="overflow-x-auto border-t border-gray-700/50">
                  <table className="w-full text-sm">
                    <thead className="bg-[#0f172a]/60">
                      <tr>
                        <th className="text-left px-5 py-3 font-medium text-gray-400 uppercase tracking-wide text-xs">Cliente</th>
                        <th className="text-right px-5 py-3 font-medium text-gray-400 uppercase tracking-wide text-xs">Débito Fiscal</th>
                        <th className="text-right px-5 py-3 font-medium text-gray-400 uppercase tracking-wide text-xs">Crédito Fiscal</th>
                        <th className="text-right px-5 py-3 font-medium text-gray-400 uppercase tracking-wide text-xs">Saldo</th>
                        <th className="text-center px-5 py-3 font-medium text-gray-400 uppercase tracking-wide text-xs">DDJJ</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700/50">
                      {data.detalle_por_cliente.map((row) => (
                        <tr key={row.client_id} className="hover:bg-white/5 transition-colors">
                          <td className="px-5 py-3 font-medium text-white">
                            {row.client_name ?? `Cliente #${row.client_id}`}
                          </td>
                          <td className="px-5 py-3 text-right text-gray-300">
                            {formatCurrency(row.debito_fiscal)}
                          </td>
                          <td className="px-5 py-3 text-right text-gray-300">
                            {formatCurrency(row.credito_fiscal)}
                          </td>
                          <td className={`px-5 py-3 text-right font-semibold ${row.saldo > 0 ? 'text-rose-400' : row.saldo < 0 ? 'text-emerald-400' : 'text-gray-500'}`}>
                            {formatCurrency(row.saldo)}
                          </td>
                          <td className="px-5 py-3 text-center">
                            {row.presentada ? (
                              <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto" />
                            ) : (
                              <span className="inline-block w-2 h-2 rounded-full bg-amber-400 mx-auto" title="Pendiente" />
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Sin datos */}
          {data.tipo === 'sin_datos' && (
            <div className="card text-center py-12">
              <AlertCircle className="w-10 h-10 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-300 font-medium">No hay registros IVA para {periodoLegible(periodo)}</p>
              <p className="text-gray-500 text-sm mt-1">
                Cargá registros IVA desde la sección <strong className="text-gray-300">Balance IVA</strong> o importá comprobantes desde <strong className="text-gray-300">Herramientas</strong>.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
