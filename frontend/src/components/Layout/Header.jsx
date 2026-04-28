import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronDown, LogOut, Users } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

export default function Header() {
  const [isOpen, setIsOpen] = useState(false)
  const { user, logout, isSuperAdmin } = useAuth()
  const navigate = useNavigate()
  const dropdownRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <header className="h-16 bg-[#0f172a] border-b border-gray-700/40 flex items-center justify-end px-6 relative">
      <div className="relative" ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-3 py-1.5 px-3 rounded-lg hover:bg-white/5 transition-colors"
        >
          <div className="text-right">
            <p className="text-sm font-medium text-white">{user?.name} {user?.last_name}</p>
            <p className="text-xs text-gray-400 capitalize">{user?.role?.replace('_', ' ')}</p>
          </div>
          <ChevronDown size={16} className={isOpen ? "text-violet-400 rotate-180" : "text-gray-400"} />
        </button>

        {isOpen && (
          <div className="absolute right-0 mt-2 w-48 bg-[#1e293b] rounded-xl border border-gray-700 shadow-xl overflow-hidden z-50">
            <div className="px-4 py-2.5 border-b border-gray-700 text-xs text-gray-500">{user?.email}</div>
            {(isSuperAdmin || user?.role === 'admin') && (
              <button
                onClick={() => { setIsOpen(false); navigate('/usuarios'); }}
                className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-gray-300 hover:bg-white/5"
              >
                <Users size={16} /> Gestión de Usuarios
              </button>
            )}
            <div className="border-t border-gray-700">
              <button
                onClick={logout}
                className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-rose-400 hover:bg-rose-500/10"
              >
                <LogOut size={16} /> Cerrar sesión
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
