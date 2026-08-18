// ============================================
// CONFIRM SUBMIT - Confirmación de acciones destructivas
// ============================================
// Reemplaza los onsubmit="return confirm(...)" inline.
// Uso: <form method="POST" data-confirm="¿Eliminar este item?">
(function () {
    'use strict';

    document.addEventListener('submit', function (e) {
        const form = e.target;
        const message = form.getAttribute('data-confirm');
        if (!message) return;

        if (!window.confirm(message)) {
            // loading.js detecta defaultPrevented y no muestra el loader
            e.preventDefault();
        }
    });
})();