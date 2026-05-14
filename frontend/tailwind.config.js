/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: '#0A0A0A',
          950: '#0A0A0A',
          900: '#141414',
          800: '#1E1E1E',
          700: '#2A2A2A',
          600: '#404040',
          500: '#555555',
          400: '#737373',
          300: '#9A9A9A',
          200: '#C8C8C8',
          100: '#E0E0E0',
          50:  '#F5F5F5',
        },
        paper: '#F7F7F7',
        border: '#E5E5E5',
        brand: {
          50:  '#FDF2F3',
          100: '#FBE5E7',
          200: '#F5BFC4',
          500: '#9D1626',
          600: '#8A1322',
          700: '#73101C',
          dark: '#DC2626',
        },
        success: { DEFAULT: '#10B981', soft: 'rgba(16,185,129,0.10)' },
        warn:    { DEFAULT: '#F59E0B', soft: 'rgba(245,158,11,0.10)' },
        danger:  { DEFAULT: '#EF4444', soft: 'rgba(239,68,68,0.10)' },
      },
      fontFamily: {
        sans:    ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Helvetica Neue', 'Segoe UI', 'sans-serif'],
        display: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Helvetica Neue', 'sans-serif'],
      },
      letterSpacing: {
        'apple-1': '-0.02em',
        'apple-2': '-0.03em',
        'apple-3': '-0.04em',
        'wide-1':  '0.12em',
        'wide-2':  '0.18em',
        'wide-3':  '0.22em',
      },
      boxShadow: {
        soft:  '0 1px 2px rgb(0 0 0 / 0.04), 0 4px 24px -8px rgb(0 0 0 / 0.06)',
        card:  '0 1px 3px rgb(0 0 0 / 0.05), 0 12px 40px -12px rgb(0 0 0 / 0.12)',
        focus: '0 0 0 4px rgb(10 10 10 / 0.06)',
      },
      borderRadius: { '4xl': '2rem' },
    },
  },
  plugins: [],
}
