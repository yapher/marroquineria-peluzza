// Configuración de Tailwind CSS
tailwind.config = {
    theme: {
        extend: {
            colors: {
                leather: { 50:'#fdf8f3', 100:'#f9ebd9', 700:'#6b3410', 900:'#3d1d08' },
                craft:   { 500:'#b87333', 600:'#9a5f28' }
            },
            fontFamily: {
                display: ['"Playfair Display"', 'serif'],
                body:    ['Inter', 'sans-serif']
            }
        }
    }
}