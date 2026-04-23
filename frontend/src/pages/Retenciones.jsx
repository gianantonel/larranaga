import { useEffect, useState } from 'react'
import { getClients } from '../utils/api'
import PageHeader from '../components/UI/PageHeader'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import RetencionesPanel from '../components/RetencionesPanel'

export default function Retenciones() {
  const [clients, setClients] = useState([])
  const [clientId, setClientId] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getClients()
      .then(r => {
        setClients(r.data)
        if (r.data.length && !clientId) setClientId(String(r.data[0].id))
      })
      .catch(err => console.error('Clients load error:', err))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="min-h-screen flex items-center justify-center"><LoadingSpinner /></div>

  const selectedClient = clients.find(c => String(c.id) === String(clientId))

  return (
    <div className="space-y-6">
      <PageHeader
        title="Retenciones y Percepciones"
        subtitle="Consulta Mis Retenciones de ARCA por cliente y período (scraping con clave fiscal)"
      />

      <div className="card p-4">
        <label className="text-xs text-gray-400 mb-1 block">Cliente</label>
        <select
          value={clientId}
          onChange={(e) => setClientId(e.target.value)}
          className="input-field w-full md:w-1/2"
        >
          <option value="">— Seleccioná cliente —</option>
          {clients.map(c => (
            <option key={c.id} value={c.id}>
              {c.name} {c.cuit ? `(${c.cuit})` : ''}
            </option>
          ))}
        </select>
        {selectedClient && !selectedClient.cuit && (
          <p className="mt-2 text-xs text-amber-400">⚠ Este cliente no tiene CUIT cargado.</p>
        )}
      </div>

      {clientId && <RetencionesPanel clientId={Number(clientId)} />}
    </div>
  )
}
