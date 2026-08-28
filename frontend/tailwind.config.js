/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navik: {
          base: '#07111F',      // Deep Navy primary background
          secondary: '#0D1B2A', // Navy Slate headers & sidebars
          card: '#13263A',      // Ocean Slate cards & panels
          cyan: '#00D4FF',      // Cyan / Aqua primary accent
          green: '#18C7A0',     // Sea Green secondary accent
          amber: '#FFB547',     // Amber warning
          coral: '#FF5C5C',     // Coral Red danger / restricted
          white: '#EAF4F8',     // Off White main text
          gray: '#8FA8B8',      // Blue Gray secondary text
          border: '#20384D',    // Muted Navy borders
        },
        slate: {
          750: '#1e293b',
          850: '#0f172a',
        }
      }
    },
  },
  plugins: [],
}
