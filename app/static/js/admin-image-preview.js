// ============================================
// ADMIN IMAGE PREVIEW - Vista previa de imágenes extra
// ============================================
// Extraído de admin/product_form.html
(function () {
    'use strict';

    function renderPreview(input) {
        const preview = document.getElementById('extra-images-preview');
        if (!preview) return;

        preview.innerHTML = '';
        const files = Array.from(input.files || []);
        if (files.length === 0) return;

        // Límite por imagen desde data-attribute (default 5MB)
        const maxSizeMB = parseFloat(input.dataset.maxSizeMb) || 5;

        // Contador de imágenes seleccionadas
        const info = document.createElement('p');
        info.className = 'text-sm text-craft-600 font-semibold w-full';
        info.textContent = files.length + ' imagen(es) seleccionada(s)';
        preview.appendChild(info);

        files.forEach(function (file) {
            const sizeMB = file.size / (1024 * 1024);
            const div = document.createElement('div');

            if (sizeMB > maxSizeMB) {
                div.innerHTML = '<div class="w-20 h-20 flex items-center justify-center rounded-lg border-2 border-red-400 bg-red-50 text-red-600 text-[10px] text-center p-1">⚠️ ' + sizeMB.toFixed(1) + 'MB</div>';
            } else {
                const reader = new FileReader();
                reader.onload = function (ev) {
                    div.innerHTML = '<img src="' + ev.target.result + '" class="w-20 h-20 object-cover rounded-lg border-2 border-gray-200">';
                };
                reader.readAsDataURL(file);
            }
            preview.appendChild(div);
        });
    }

    function init() {
        const input = document.getElementById('extra-images-input');
        if (!input) return;
        input.addEventListener('change', function () {
            renderPreview(this);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();