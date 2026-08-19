// ============================================
// MOBILE MENU - Cierre automático del menú móvil
// ============================================
// Cierra el menú cuando el usuario toca cualquier enlace de navegación.
// Se comunica con Alpine.js mediante un CustomEvent para mantener
// el desacoplamiento entre el JS y los templates.
(function () {
    'use strict';

    var EVENT_NAME = 'mobile-menu:close';

    function closeMenu() {
        window.dispatchEvent(new CustomEvent(EVENT_NAME));
    }

    function init() {
        var panel = document.querySelector('.mobile-menu-panel');
        if (!panel) return;

        // Delegación de eventos: cualquier <a> con href válido dentro del panel
        // cierra el menú automáticamente.
        panel.addEventListener('click', function (e) {
            var link = e.target.closest('a[href]');
            if (!link) return;

            var href = link.getAttribute('href');

            // Ignorar toggles internos (href="#" o javascript:)
            if (!href || href === '#' || href.indexOf('javascript:') === 0) return;

            closeMenu();
        });

        // Fallback: si la página se restaura desde bfcache
        // (botón "atrás" del móvil), cerrar el menú.
        window.addEventListener('pageshow', function (event) {
            if (event.persisted) {
                closeMenu();
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();