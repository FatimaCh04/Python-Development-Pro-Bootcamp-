/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: '#0F1115',
          50: '#F5F3EE',
        },
        surface: {
          DEFAULT: '#171A21',
          2: '#1F232C',
          3: '#272B36',
        },
        signal: {
          DEFAULT: '#6C5CE7',
          bright: '#8A7CFF',
          dim: '#4A3FA6',
        },
        pulse: {
          DEFAULT: '#00D9C0',
          dim: '#0A9E8D',
        },
        amber: {
          DEFAULT: '#FFB454',
        },
        muted: '#9AA0AC',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"Inter"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 40px -10px rgba(108, 92, 231, 0.45)',
        'glow-pulse': '0 0 30px -8px rgba(0, 217, 192, 0.5)',
        card: '0 1px 0 rgba(255,255,255,0.04) inset, 0 8px 24px -12px rgba(0,0,0,0.6)',
      },
      keyframes: {
        heartbeat: {
          '0%, 100%': { transform: 'scale(1)' },
          '25%': { transform: 'scale(1.35)' },
          '40%': { transform: 'scale(0.9)' },
          '55%': { transform: 'scale(1.2)' },
          '70%': { transform: 'scale(1)' },
        },
        dash: {
          to: { strokeDashoffset: '0' },
        },
        floatUp: {
          '0%': { opacity: 0, transform: 'translateY(10px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      animation: {
        heartbeat: 'heartbeat 0.6s cubic-bezier(.4,0,.2,1)',
        dash: 'dash 2.4s ease-out forwards',
        floatUp: 'floatUp 0.4s ease-out both',
        shimmer: 'shimmer 2.5s linear infinite',
      },
    },
  },
  plugins: [],
}
