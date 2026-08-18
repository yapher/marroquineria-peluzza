// ============================================
// ADMIN ORDER STATUS - Campo de tracking condicional
// ============================================
// Extraído de admin/order_detail.html
(function () {
    'use strict';

    function toggleTrackingField(status) {
        const field = document.getElementById('tracking-field');
        if (!field) return;
        if (status === 'shipped') {
            field.classList.remove('hidden');
        } else {
            field.classList.add('hidden');
        }
    }

    function init() {
        const statusSelect = document.getElementById('status-select');
        if (!statusSelect) return;

        statusSelect.addEventListener('change', function () {
            toggleTrackingField(this.value);
        });

        // Estado inicial por si el select ya trae un valor preseleccionado
        toggleTrackingField(statusSelect.value);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();