/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{tsx,ts,jsx,js}'],
  theme: {
    extend: {
      colors: {
        primary: { 50:'#eff6ff',100:'#dbeafe',200:'#bfdbfe',300:'#93c5fd',400:'#60a5fa',500:'#3b82f6',600:'#2563eb',700:'#1d4ed8',800:'#1e40af',900:'#1e3a8a',950:'#172554' },
        surface: { 50:'#f8fafc',100:'#f1f5f9',200:'#e2e8f0',300:'#cbd5e1',400:'#94a3b8',500:'#64748b',600:'#475569',700:'#334155',800:'#1e293b',850:'#172033',900:'#0f172a',950:'#020617' },
        accent:  { 400:'#a78bfa',500:'#8b5cf6',600:'#7c3aed' },
        bull: '#22c55e',
        bear: '#ef4444',
        side: '#f59e0b',
      },
      fontFamily: { sans: ['Inter','system-ui','sans-serif'], mono: ['JetBrains Mono','monospace'] },
      boxShadow: { glow: '0 0 20px rgb(59 130 246 / 0.35)', 'card-lg': '0 4px 24px 0 rgb(0 0 0 / 0.12)' },
      animation: { 'fade-in':'fadeIn .3s ease-out', 'slide-up':'slideUp .35s cubic-bezier(.16,1,.3,1)', skeleton:'skeleton 1.4s ease-in-out infinite' },
      keyframes: {
        fadeIn:  { from:{opacity:'0'}, to:{opacity:'1'} },
        slideUp: { from:{opacity:'0',transform:'translateY(16px)'}, to:{opacity:'1',transform:'translateY(0)'} },
        skeleton:{ '0%,100%':{opacity:'.5'}, '50%':{opacity:'1'} },
      },
    },
  },
  plugins: [],
}
