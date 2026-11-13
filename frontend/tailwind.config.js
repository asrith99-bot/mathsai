/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Platform dark theme
        bg: {
          primary:   '#0a0a0f',
          secondary: '#12121a',
          card:      '#1a1a28',
          border:    '#2a2a3d',
        },
        signal: {
          buy:       '#00d084',
          'buy-dim': '#003d20',
          sell:      '#ff4d4d',
          'sell-dim':'#4d0000',
          hold:      '#8b8b9b',
          'hold-dim':'#2a2a3d',
        },
        accent:  '#6c63ff',
        muted:   '#5a5a7a',
        surface: '#1f1f2e',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-green': 'pulseGreen 1s ease-in-out infinite',
        'pulse-red':   'pulseRed 1s ease-in-out infinite',
        'fade-in':     'fadeIn 0.3s ease-in-out',
      },
      keyframes: {
        pulseGreen: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(0, 208, 132, 0.4)' },
          '50%':      { boxShadow: '0 0 0 6px rgba(0, 208, 132, 0)' },
        },
        pulseRed: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(255, 77, 77, 0.4)' },
          '50%':      { boxShadow: '0 0 0 6px rgba(255, 77, 77, 0)' },
        },
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(-4px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
