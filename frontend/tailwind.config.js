/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Plant console palette — carried over from the ESCA HSE mockup.
        steel: { DEFAULT: '#0B1526', 2: '#122036', 3: '#1B2E4A' },
        line: '#27405F',
        hi: { DEFAULT: '#9E1B32', 2: '#C42440', dim: '#5E101D' },
        safe: '#38B87C',
        warn: '#F09030',
        crit: '#E0483C',
        info: '#4A9DD8',
        txt: { DEFAULT: '#E9EFF7', 2: '#93A9C4', 3: '#5E7794' },
      },
      fontFamily: {
        sans: ['"IBM Plex Sans Arabic"', 'Segoe UI', 'Tahoma', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'Consolas', 'monospace'],
      },
      fontSize: {
        // The console runs denser than Tailwind's defaults.
        '2xs': ['10.5px', '1.5'],
        xs: ['11.5px', '1.6'],
        sm: ['12.5px', '1.65'],
        base: ['14px', '1.6'],
      },
      borderRadius: { DEFAULT: '4px', md: '5px', lg: '7px' },
      keyframes: {
        blip: { '0%,100%': { opacity: 1 }, '50%': { opacity: 0.35 } },
        fade: { from: { opacity: 0, transform: 'translateY(6px)' }, to: { opacity: 1, transform: 'none' } },
        pop: { from: { opacity: 0, transform: 'scale(.95) translateY(14px)' }, to: { opacity: 1, transform: 'none' } },
        pulseRing: {
          '0%,100%': { boxShadow: '0 0 0 0 rgba(224,72,60,.4)' },
          '50%': { boxShadow: '0 0 0 7px rgba(224,72,60,0)' },
        },
      },
      animation: {
        blip: 'blip 2s infinite',
        fade: 'fade .25s ease-out',
        pop: 'pop .22s ease-out',
        'pulse-ring': 'pulseRing 2.4s infinite',
      },
    },
  },
  plugins: [],
}
