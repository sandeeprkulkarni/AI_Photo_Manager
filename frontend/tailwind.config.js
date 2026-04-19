/** @type {import('tailwindcss').Config} */
export default {
  // CRITICAL: Tailwind 3.x requires this to scan your files
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "var(--border)",
        background: "var(--background)",
        foreground: "var(--foreground)",
        sidebar: {
          DEFAULT: "var(--sidebar)",
          foreground: "var(--sidebar-foreground)",
          primary: "var(--sidebar-primary)",
          border: "var(--sidebar-border)",
          accent: "var(--sidebar-accent)",
        }
      },
    },
  },
  plugins: [],
}