/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Plant console palette — now driven by CSS variables so themes can swap them.
        // The rgb(var(--c-x) / <alpha-value>) pattern lets Tailwind opacity modifiers work.
        steel: {
          DEFAULT: 'rgb(var(--c-steel) / <alpha-value>)',
          1: 'rgb(var(--c-steel) / <alpha-value>)',
          2: 'rgb(var(--c-steel2) / <alpha-value>)',
          3: 'rgb(var(--c-steel3) / <alpha-value>)',
        },
        line: 'rgb(var(--c-line) / <alpha-value>)',
        hi: {
          DEFAULT: 'rgb(var(--c-hi) / <alpha-value>)',
          2: 'rgb(var(--c-hi2) / <alpha-value>)',
          dim: 'rgb(var(--c-hi-dim) / <alpha-value>)',
          txt: 'rgb(var(--c-hi-txt) / <alpha-value>)',
        },
        safe: 'rgb(var(--c-safe) / <alpha-value>)',
        warn: 'rgb(var(--c-warn) / <alpha-value>)',
        crit: 'rgb(var(--c-crit) / <alpha-value>)',
        info: 'rgb(var(--c-info) / <alpha-value>)',
        txt: {
          DEFAULT: 'rgb(var(--c-txt) / <alpha-value>)',
          2: 'rgb(var(--c-txt2) / <alpha-value>)',
          3: 'rgb(var(--c-txt3) / <alpha-value>)',
        },
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
