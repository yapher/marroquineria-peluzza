// Configuración de Tailwind CSS
tailwind.config = {
  theme: {
    extend: {
      colors: {
        leather: {
          50:  '#fdf8f3',
          100: '#f9ebd9',
          200: '#f0d9bc',
          300: '#e4c199',
          400: '#d4a574',
          500: '#c4884f',
          600: '#9a5f28',
          700: '#6b3410',
          800: '#4a2510',
          900: '#3d1d08',
          950: '#2a1205'
        },
        craft: {
          400: '#d4956a',
          500: '#b87333',
          600: '#9a5f28',
          700: '#7d4c1f'
        }
      },
      fontFamily: {
        display: ['"Playfair Display"', 'serif'],
        body:    ['Inter', 'sans-serif']
      },
      boxShadow: {
        'warm': '0 4px 20px rgba(61, 29, 8, 0.08)',
        'warm-lg': '0 8px 30px rgba(61, 29, 8, 0.12)',
        'warm-xl': '0 20px 40px rgba(61, 29, 8, 0.15)',
      }
    }
  }
}