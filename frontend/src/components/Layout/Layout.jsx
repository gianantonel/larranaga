import { useState, useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Menu } from 'lucide-react'
import Sidebar from './Sidebar'
import Logo from '../UI/Logo'
import ThemeToggle from '../UI/ThemeToggle'

export default function Layout() {
  const [open, setOpen] = useState(false)
  const location = useLocation()

  useEffect(() => { setOpen(false) }, [location.pathname])

  useEffect(() => {
    const mq = window.matchMedia('(min-width: 1024px)')
    const handler = (e) => { if (e.matches) setOpen(false) }
    mq.addEventListener?.('change', handler)
    return () => mq.removeEventListener?.('change', handler)
  }, [])

  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  return (
    <div className="flex min-h-screen" style={{ background: 'var(--bg)' }}>
      <Sidebar open={open} onClose={() => setOpen(false)} />

      {open && (
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-sm z-30 lg:hidden"
          onClick={() => setOpen(false)}
          aria-label="Cerrar menú"
        />
      )}

      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar mobile */}
        <header
          className="lg:hidden sticky top-0 z-20 flex items-center justify-between gap-3 px-4 h-14 backdrop-blur"
          style={{
            background: 'color-mix(in srgb, var(--bg) 85%, transparent)',
            borderBottom: '1px solid var(--border)',
          }}
        >
          <div className="flex items-center gap-3">
            <button
              onClick={() => setOpen(true)}
              className="p-2 -ml-2 rounded-full hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
              style={{ color: 'var(--text)' }}
              aria-label="Abrir menú"
            >
              <Menu size={20} />
            </button>
            <Logo size="sm" showSubtitle={false} />
          </div>
          <ThemeToggle />
        </header>

        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
