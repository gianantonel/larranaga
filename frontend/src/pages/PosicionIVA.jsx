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

  // Configuración visual según tipo de posición
  const config = {
    deuda: {
      color: 'text-red-600',
      bg: 'bg-red-50 border-red-200',
      badge: 'bg-red-100 text-red-700',
      icon: <TrendingUp className="w-8 h-8 text-red-500" />,
      label: 'Deuda con AFIP',
    },
    a_favor: {
      color: 'text-green-600',
      bg: 'bg-green-50 border-green-200',
      badge: 'bg-green-100 text-green-700',
      icon: <TrendingDown className="w-8 h-8 text-green-500" />,
      label: 'Saldo a favor',
    },
    neutro: {
      color: 'text-gray-600',
      bg: 'bg-gray-50 border-gray-200',
      badge: 'bg-gray-100 text-gray-700',
      icon: <Minus className="w-8 h-8 text-gray-400" />,
      label: 'Posición neutra',
    },
    sin_datos: {
      color: 'text-gray-400',
      bg: 'bg-gray-50 border-gray-200',
      badge: 'bg-gray-100 text-gray-500',
      icon: <AlertCircle className="w-8 h-8 text-gray-400" />,
      label: 'Sin datos',
    },
  }

  const tipo = data?.tipo ?? 'sin_datos'
  const cfg = config[tipo] ?? config.sin_datos

  // Formato legible del período "2026-02" → "Febrero 2026"
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
      <div className="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-4">
        <label className="text-sm font-medium text-gray-700 whitespace-nowrap">Período:</label>
        <input
          type="month"
          value={periodo}
          onChange={handlePeriodo}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <span className="text-sm text-gray-500 capitalize">{periodoLegible(periodo)}</span>
      </div>

      {loading && (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3 text-red-700 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          {error}
        </div>
      )}

      {data && !loading && (
        <>
          {/* Tarjetas principales */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Débito fiscal */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
                IVA Débito Fiscal
              </p>
              <p className="text-2xl font-bold text-gray-800">
                {formatCurrency(data.debito_fiscal)}
              </p>
              <p className="text-xs text-gray-400 mt-1">IVA generado por ventas</p>
            </div>

            {/* Crédito fiscal */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
                IVA Crédito Fiscal
              </p>
              <p className="text-2xl font-bold text-gray-800">
                {formatCurrency(data.credito_fiscal)}
              </p>
              <p className="text-xs text-gray-400 mt-1">IVA deducible por compras</p>
            </div>

            {/* Posición del mes */}
            <div className={`rounded-xl border p-5 ${cfg.bg}`}>
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Posición del Mes
                </p>
                {cfg.icon}
              </div>
              <p className={`text-2xl font-bold ${cfg.color}`}>
                {formatCurrency(Math.abs(data.posicion))}
              </p>
              <span className={`inline-block mt-2 text-xs font-semibold px-2 py-0.5 rounded-full ${cfg.badge}`}>
                {cfg.label}
              </span>
            </div>
          </div>

          {/* Detalle por cliente (colapsable) */}
          {data.clientes_incluidos > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <button
                className="w-full flex items-center justify-between px-5 py-4 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
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
                <div className="overflow-x-auto border-t border-gray-100">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="text-left px-5 py-3 font-medium text-gray-500">Cliente</th>
                        <th className="text-right px-5 py-3 font-medium text-gray-500">Débito Fiscal</th>
                        <th className="text-right px-5 py-3 font-medium text-gray-500">Crédito Fiscal</th>
                        <th className="text-right px-5 py-3 font-medium text-gray-500">Saldo</th>
                        <th className="text-center px-5 py-3 font-medium text-gray-500">DDJJ</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {data.detalle_por_cliente.map((row) => (
                        <tr key={row.client_id} className="hover:bg-gray-50 transition-colors">
                          <td className="px-5 py-3 font-medium text-gray-800">
                            {row.client_name ?? `Cliente #${row.client_id}`}
                          </td>
                          <td className="px-5 py-3 text-right text-gray-700">
                            {formatCurrency(row.debito_fiscal)}
                          </td>
                          <td className="px-5 py-3 text-right text-gray-700">
                            {formatCurrency(row.credito_fiscal)}
                          </td>
                          <td className={`px-5 py-3 text-right font-semibold ${row.saldo > 0 ? 'text-red-600' : row.saldo < 0 ? 'text-green-600' : 'text-gray-500'}`}>
                            {formatCurrency(row.saldo)}
                          </td>
                          <td className="px-5 py-3 text-center">
                            {row.presentada ? (
                              <CheckCircle2 className="w-4 h-4 text-green-500 mx-auto" />
                            ) : (
                              <span className="inline-block w-2 h-2 rounded-full bg-yellow-400 mx-auto" title="Pendiente" />
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
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
              <AlertCircle className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 font-medium">No hay registros IVA para {periodoLegible(periodo)}</p>
              <p className="text-gray-400 text-sm mt-1">
                Cargá registros IVA desde la sección <strong>IVA</strong> o importá comprobantes desde <strong>Herramientas</strong>.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
