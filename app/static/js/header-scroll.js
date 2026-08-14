// ============================================
// HEADER SCROLL EFFECT - Glassmorphism
// ============================================
(function() {
    'use strict';
    
    const header = document.querySelector('header');
    let lastScroll = 0;
    
    if (!header) return;
    
    function handleScroll() {
        const currentScroll = window.pageYOffset;
        
        // Agregar clase glass al hacer scroll
        if (currentScroll > 50) {
            header.classList.add('header-glass');
        } else {
            header.classList.remove('header-glass');
        }
        
        lastScroll = currentScroll;
    }
    
    // Throttle para mejor performance
    let ticking = false;
    window.addEventListener('scroll', function() {
        if (!ticking) {
            window.requestAnimationFrame(function() {
                handleScroll();
                ticking = false;
            });
            ticking = true;
        }
    }, { passive: true });
    
    // Inicializar
    handleScroll();
})();