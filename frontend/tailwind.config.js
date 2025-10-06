/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Three Realms Color System
        // Based on DESIGN_PRINCIPLES.md
        realm: {
          // Corporeal Realm (Physical/Grounding)
          corporeal: {
            DEFAULT: '#2D7D6E',
            light: '#4A9B8E',
            lighter: '#6DBFB3',
            dark: '#1E5A4F',
          },
          // Objective/Symbolic Realm (Constructed/Abstract)
          symbolic: {
            DEFAULT: '#6B46C1',
            light: '#8B5CF6',
            lighter: '#A78BFA',
            dark: '#553399',
          },
          // Subjective/Conscious Realm (Presence/Awareness)
          subjective: {
            DEFAULT: '#1E1B4B',
            light: '#312E81',
            lighter: '#4C1D95',
            dark: '#0F0D26',
          },
        },
      },
      fontFamily: {
        // Philosophical font system
        'contemplative': ['Crimson Pro', 'Lora', 'Georgia', 'serif'], // Subjective realm
        'structural': ['Inter', 'Source Sans 3', 'system-ui', 'sans-serif'], // Symbolic realm
        'grounded': ['JetBrains Mono', 'Fira Code', 'monospace'], // Corporeal realm
      },
    },
  },
  plugins: [],
}
