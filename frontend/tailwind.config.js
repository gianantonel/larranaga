/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',                          // ← toggle por clase .dark
  theme: {
    extend: {
      colors: {
        // ─── Paleta Larrañaga (basada en logo + sitio estudiolarranaga.com) ──
        brand: {
          50:  '#FDF2F3',
          100: '#FBE5E7',
          200: '#F5BFC4',
          300: '#EE99A1',
          400: '#DC525E',
          500: '#9D1626',   // ← rojo Larrañaga (logo "A")
          600: '#8A1322',
          700: '#73101C',
          800: '#5C0D16',
          900: '#3D0810',
          dark: '#DC2626',  // ← variante para dark mode (contraste)
        },
        // Surface tokens (usar via clases dark:)
        surface: {
          50:  '#FAFAFA',   // light bg
          100: '#F5F5F5',
          200: '#E4E4E7',
          300: '#D4D4D8',
          900: '#171717',   // dark surface
          950: '#0A0A0A',   // dark bg
        },
        ink: {
          DEFAULT: '#0C0C0C', // text light mode
          muted: '#525252',
          subtle: '#737373',
          on: '#FAFAFA',      // text dark mode
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'SF Pro Text', 'Segoe UI', 'sans-serif'],
        display: ['Inter', '-apple-system', 'sans-serif'],
      },
      letterSpacing: {
        'tight-2': '-0.02em',
        'tight-3': '-0.03em',
      },
      boxShadow: {
        soft: '0 1px 2px rgb(0 0 0 / 0.04), 0 4px 24px -8px rgb(0 0 0 / 0.06)',
        card: '0 1px 3px rgb(0 0 0 / 0.05), 0 12px 40px -12px rgb(0 0 0 / 0.12)',
        glow: '0 0 0 4px rgb(157 22 38 / 0.08)',
      },
      borderRadius: {
        '4xl': '2rem',
      },
    },
  },
  plugins: [],
}
