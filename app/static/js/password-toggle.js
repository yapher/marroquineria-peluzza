// ============================================
// PASSWORD TOGGLE - Mostrar/ocultar contraseña
// ============================================
// Agrega un botón de ojito a cualquier input con
// el atributo data-password-toggle.
(function () {
  'use strict';

  var ICON_SHOW = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>';

  var ICON_HIDE = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/></svg>';

  function init() {
    var inputs = document.querySelectorAll('[data-password-toggle]');

    inputs.forEach(function (input) {
      // Evitar agregar el botón dos veces
      if (input.dataset.toggleAttached) return;
      input.dataset.toggleAttached = 'true';

      // Crear contenedor relativo si el input no lo tiene
      var wrapper = input.parentElement;
      if (!wrapper.classList.contains('relative')) {
        wrapper.classList.add('relative');
      }

      // Crear botón
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.setAttribute('aria-label', 'Mostrar contraseña');
      btn.className = 'password-toggle-btn absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-craft-600 transition p-1';
      btn.innerHTML = ICON_SHOW;

      btn.addEventListener('click', function () {
        var isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';
        btn.innerHTML = isPassword ? ICON_HIDE : ICON_SHOW;
        btn.setAttribute('aria-label', isPassword ? 'Ocultar contraseña' : 'Mostrar contraseña');
        input.focus();
      });

      wrapper.appendChild(btn);

      // Agregar padding-right al input para que el texto no quede bajo el icono
      input.style.paddingRight = '2.75rem';
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();