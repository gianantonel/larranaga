import { useState, useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Menu, Scale } from 'lucide-react'
import Sidebar from './Sidebar'

export default function Layout() {
  const [open, setOpen] = useState(false)
  const location = useLocation()

  // Cerrar drawer al navegar
  useEffect(() => { setOpen(false) }, [location.pathname])

  // Cerrar drawer al pasar a >=lg (1024px)
  useEffect(() => {
    const mq = window.matchMedia('(min-width: 1024px)')
    const handler = (e) => { if (e.matches) setOpen(false) }
    mq.addEventListener?.('change', handler)
    return () => mq.removeEventListener?.('change', handler)
  }, [])

  // Bloquear scroll del body cuando el drawer está abierto
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  return (
    <div className="flex min-h-screen bg-[#0a0f1e]">
      <Sidebar open={open} onClose={() => setOpen(false)} />

      {open && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 lg:hidden"
          onClick={() => setOpen(false)}
          aria-label="Cerrar menú"
        />
      )}

      <div className="flex-1 flex flex-col min-w-0">
        <header className="lg:hidden sticky top-0 z-20 flex items-center gap-3 bg-[#0f172a]/95 backdrop-blur border-b border-gray-700/40 px-4 h-14">
          <button
            onClick={() => setOpen(true)}
            className="p-2 -ml-2 rounded-lg hover:bg-white/5 text-gray-200 transition-colors"
            aria-label="Abrir menú"
          >
            <Menu size={22} />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center">
              <Scale size={16} className="text-white" />
            </div>
            <h1 className="text-base font-bold text-white">Larrañaga</h1>
          </div>
        </header>

        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
