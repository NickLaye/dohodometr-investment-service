/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "xs": "475px",
        "2xl": "1400px",
      },
    },
    extend: {
      // Дизайн-система "Доходометр" - Фирменные цвета
      colors: {
        // Основная палитра Доходометр
        'dohodometr': {
          'primary': '#1F3B35',        // Глубоко-изумрудный
          'accent-1': '#C79A63',       // Медно-песочный  
          'accent-2': '#63B8A7',       // Свежий мятный
          'neutral-light': '#F8F9F8',  // Нейтральный светлый
          'neutral-dark': '#2C2E2D',   // Нейтральный тёмный
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        success: {
          DEFAULT: "hsl(142, 76%, 36%)",
          foreground: "hsl(138, 76%, 97%)",
        },
        warning: {
          DEFAULT: "hsl(32, 95%, 44%)",
          foreground: "hsl(48, 96%, 89%)",
        },
        info: {
          DEFAULT: "hsl(217, 91%, 60%)",
          foreground: "hsl(210, 40%, 98%)",
        },
        
        // Переопределяем shadcn/ui цвета для "Доходометр"
        primary: {
          DEFAULT: "var(--primary)",  // Изумрудный как основной
          foreground: "var(--neutral-light)",
        },
        secondary: {
          DEFAULT: "var(--accent-1)",  // Песочный как вторичный
          foreground: "var(--primary)",
        },
        accent: {
          DEFAULT: "var(--accent-2)",  // Мятный как акцент
          foreground: "var(--primary)",
        },
        
        // Дополнительные цвета дизайн-системы
        'accent-1': 'var(--accent-1)',
        'accent-2': 'var(--accent-2)',
        'neutral-light': 'var(--neutral-light)',
        'neutral-dark': 'var(--neutral-dark)',
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
        "fade-in": {
          "0%": { opacity: 0 },
          "100%": { opacity: 1 },
        },
        "fade-out": {
          "0%": { opacity: 1 },
          "100%": { opacity: 0 },
        },
        "slide-in-from-top": {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(0)" },
        },
        "slide-in-from-bottom": {
          "0%": { transform: "translateY(100%)" },
          "100%": { transform: "translateY(0)" },
        },
        "slide-in-from-left": {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(0)" },
        },
        "slide-in-from-right": {
          "0%": { transform: "translateX(100%)" },
          "100%": { transform: "translateX(0)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in": "fade-in 0.5s ease-in-out",
        "fade-out": "fade-out 0.5s ease-in-out",
        "slide-in-from-top": "slide-in-from-top 0.3s ease-out",
        "slide-in-from-bottom": "slide-in-from-bottom 0.3s ease-out",
        "slide-in-from-left": "slide-in-from-left 0.3s ease-out",
        "slide-in-from-right": "slide-in-from-right 0.3s ease-out",
      },
      fontFamily: {
        // Дизайн-система "Доходометр"
        'primary': ['Manrope', 'Inter', 'ui-sans-serif', 'system-ui'],
        'accent': ['Roboto Serif Narrow', 'Georgia', 'serif'],
        sans: ["Manrope", "Inter", "ui-sans-serif", "system-ui"],
        serif: ["Roboto Serif Narrow", "Georgia", "serif"],
        mono: ["JetBrains Mono", "Fira Code", "ui-monospace", "SFMono-Regular"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "0.75rem" }],
      },
      spacing: {
        "18": "4.5rem",
        "88": "22rem",
        "128": "32rem",
        "144": "36rem",
      },
      zIndex: {
        "60": "60",
        "70": "70",
        "80": "80",
        "90": "90",
        "100": "100",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
