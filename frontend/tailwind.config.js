/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#135bec',
          dark: '#0f4bc9',
        },
        accent: {
          teal: '#14b8a6',
        },
        background: {
          light: '#f6f6f8',
          dark: '#0e1117',
        },
        surface: {
          dark: '#1a1c23',
          border: '#2d3748',
        },
      },
      fontFamily: {
        display: ['Inter', 'sans-serif'],
        body: ['Noto Sans', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
