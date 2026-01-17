/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        // Dark theme colors from reference
        slate: {
          850: '#0f172a',
          900: '#0f172a',
          950: '#020617',
        },
      },
      backgroundImage: {
        'dark-gradient': 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        'dark-gradient-reverse': 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        'blue-purple': 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
        'white-gray': 'linear-gradient(135deg, #fff 0%, #cbd5e1 100%)',
      },
    },
  },
  plugins: [],
}
