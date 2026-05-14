import { Sun, Moon } from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'

export default function ThemeToggle({ className = '' }) {
  const { theme, toggle } = useTheme()
  const isDark = theme === 'dark'
  return (
    <button
      onClick={toggle}
      aria-label={isDark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
      title={isDark ? 'Modo claro' : 'Modo oscuro'}
      className={`relative inline-flex h-9 w-9 items-center justify-center rounded-full
                  transition-all duration-200 hover:bg-black/5 dark:hover:bg-white/5 ${className}`}
    >
      <Sun
        size={18}
        className={`absolute transition-all duration-300 ${
          isDark ? 'opacity-0 -rotate-90 scale-50' : 'opacity-100 rotate-0 scale-100'
        }`}
        style={{ color: 'var(--text)' }}
      />
      <Moon
        size={18}
        className={`absolute transition-all duration-300 ${
          isDark ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 rotate-90 scale-50'
        }`}
        style={{ color: 'var(--text)' }}
      />
    </button>
  )
}
