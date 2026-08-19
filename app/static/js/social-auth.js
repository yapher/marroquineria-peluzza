// ============================================
// SOCIAL AUTH - Previene doble click en login social
// ============================================
// El loader global (loading.js) ya muestra feedback; este script
// agrega un estado de carga inmediato al botón y bloquea re-clicks.
(function () {
'use strict';
document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-social-login]');
    if (!btn || btn.classList.contains('is-loading')) return;
    btn.classList.add('is-loading');
});
})();