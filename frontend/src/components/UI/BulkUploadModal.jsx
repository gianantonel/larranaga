import { X } from 'lucide-react'
import BulkUpload from './BulkUpload'

const ENTITY_LABELS = {
  clients: 'Clientes',
  collaborators: 'Colaboradores',
  tasks: 'Tareas',
  invoices: 'Facturas',
}

export default function BulkUploadModal({ open, onClose, entity }) {
  if (!open) return null

  const label = ENTITY_LABELS[entity] || entity

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="bg-[#111827] border border-gray-700/60 rounded-2xl w-full max-w-2xl shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700/50">
          <h2 className="text-lg font-bold text-white">Carga Masiva — {label}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-white/5"
            aria-label="Cerrar"
          >
            <X size={20} />
          </button>
        </div>
        <div className="p-6">
          <BulkUpload entity={entity} />
        </div>
      </div>
    </div>
  )
}
