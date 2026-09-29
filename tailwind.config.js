/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        tunis: {
          blue: '#0071e3',
          red: '#E30613',
          green: '#34C759',
          orange: '#FF9500',
          yellow: '#FFCF06',
          purple: '#A736A8'
        }
      },
      fontFamily: {
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
