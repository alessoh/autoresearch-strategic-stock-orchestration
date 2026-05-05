/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ensemble: "#534AB7",
        momentum: "#F0997B",
        meanrev: "#5DCAA5",
        buyhold: "#9CA3AF",
      },
    },
  },
  plugins: [],
};
