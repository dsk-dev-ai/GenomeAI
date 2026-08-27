import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        genome: {
          50: '#eef4ff',
          100: '#dce7fd',
          200: '#c0d5fc',
          300: '#97bafa',
          400: '#6698f5',
          500: '#3f77ef',
          600: '#2a5ae3',
          700: '#2246d0',
          800: '#213ba9',
          900: '#203585',
          950: '#172254',
        },
      },
      fontFamily: {
        sans: [
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'Roboto',
          'Inter',
          'sans-serif',
        ],
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out both',
        'fade-in-up': 'fadeInUp 0.6s ease-out both',
        'fade-in-down': 'fadeInDown 0.6s ease-out both',
        'scale-in': 'scaleIn 0.4s ease-out both',
        'slide-in-right': 'slideInRight 0.4s ease-out both',
        'shimmer': 'shimmer 1.8s linear infinite',
        'float': 'float 6s ease-in-out infinite',
        'pulse-ring': 'pulseRing 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'gradient-x': 'gradientX 8s ease infinite',
        'spin-slow': 'spin 3s linear infinite',
        'blob': 'blob 18s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInDown: {
          '0%': { opacity: '0', transform: 'translateY(-16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.96)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(24px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-600px 0' },
          '100%': { backgroundPosition: '600px 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-12px)' },
        },
        pulseRing: {
          '0%': { transform: 'scale(0.9)', opacity: '0.7' },
          '70%, 100%': { transform: 'scale(1.6)', opacity: '0' },
        },
        gradientX: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        blob: {
          '0%, 100%': { transform: 'translate(0px, 0px) scale(1)' },
          '33%': { transform: 'translate(30px, -40px) scale(1.1)' },
          '66%': { transform: 'translate(-20px, 20px) scale(0.95)' },
        },
      },
      boxShadow: {
        glow: '0 0 30px 0 rgba(63, 119, 239, 0.25)',
        'glow-lg': '0 0 60px 0 rgba(63, 119, 239, 0.35)',
        card: '0 4px 20px rgba(0, 0, 0, 0.06)',
        'card-hover': '0 12px 40px rgba(63, 119, 239, 0.15)',
      },
    },
  },
  plugins: [],
}

export default config
