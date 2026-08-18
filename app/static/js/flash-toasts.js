// ============================================
// FLASH TOASTS - Animación de notificaciones
// ============================================
// Extraído de partials/flash_messages.html
(function () {
    'use strict';

    function dismissToast(toast) {
        if (!toast || toast.dataset.dismissing) return;
        toast.dataset.dismissing = 'true';
        toast.classList.remove('translate-x-0', 'opacity-100');
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(function () { toast.remove(); }, 500);
    }

    function initToasts() {
        const toasts = document.querySelectorAll('.flash-toast');

        toasts.forEach(function (toast, index) {
            // Entrada escalonada
            setTimeout(function () {
                toast.classList.remove('translate-x-full', 'opacity-0');
                toast.classList.add('translate-x-0', 'opacity-100');
            }, 100 + (index * 100));

            // Duración desde data-attribute
            const duration = parseInt(toast.dataset.duration) || 5000;

            // Barra de progreso
            const progressBar = toast.querySelector('.flash-progress');
            if (progressBar) {
                progressBar.style.transition = 'transform ' + duration + 'ms linear';
                requestAnimationFrame(function () {
                    requestAnimationFrame(function () {
                        progressBar.style.transform = 'scaleX(0)';
                    });
                });
            }

            // Auto-cerrar
            setTimeout(function () {
                dismissToast(toast);
            }, duration);
        });
    }

    // Cierre manual (delegado → funciona también con toasts inyectados por HTMX)
    document.addEventListener('click', function (e) {
        const closeBtn = e.target.closest('.flash-close');
        if (!closeBtn) return;
        dismissToast(closeBtn.closest('.flash-toast'));
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initToasts);
    } else {
        initToasts();
    }
})();