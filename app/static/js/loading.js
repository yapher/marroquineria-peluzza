// ============================================
// LOADING GLOBAL - Marroquinería Artesanal
// ============================================
(function() {
    const loader = document.getElementById('global-loader');
    const progressBar = document.getElementById('progress-bar');

    // Función helper para mostrar loader
    function showLoader(message = 'Cargando...') {
        if (loader && window.Alpine) {
            Alpine.$data(loader).message = message;
        }
        loader?.classList.add('active');
        progressBar?.classList.add('active');
        progressBar?.classList.remove('complete');
    }

    function hideLoader() {
        loader?.classList.remove('active');
        progressBar?.classList.add('complete');
        setTimeout(() => {
            progressBar?.classList.remove('active', 'complete');
            progressBar.style.width = '0%';
        }, 700);
    }

    // ============================================
    // 1. Loading al cambiar de página (navegación normal)
    // ============================================
    window.addEventListener('beforeunload', function(e) {
        if (!window._htmxRequest && !window._formSubmitting) {
            showLoader('Cargando página...');
        }
    });

    // ============================================
    // 2. Loading para clicks en enlaces normales
    // ============================================
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a[href]');
        if (!link) return;

        const href = link.getAttribute('href');
        if (!href ||
            href.startsWith('#') ||
            href.startsWith('javascript:') ||
            link.hasAttribute('hx-get') ||
            link.hasAttribute('hx-post') ||
            link.hasAttribute('hx-delete') ||
            link.hasAttribute('hx-put') ||
            link.getAttribute('target') === '_blank' ||
            link.hasAttribute('download') ||
            (href.startsWith('http') && !href.includes(window.location.hostname))) {
            return;
        }

        // ✅ NO mostrar loader si es una descarga de archivo
        const downloadExtensions = ['.csv', '.pdf', '.xlsx', '.xls', '.zip', '.doc', '.docx'];
        const isDownload = downloadExtensions.some(ext => href.toLowerCase().includes(ext));
        if (isDownload) return;

        showLoader('Cargando página...');
    });

    // ============================================
    // 3. Loading para formularios
    // ============================================
    document.addEventListener('submit', function(e) {
        const form = e.target;

        // ✅ Submit cancelado (ej: confirmación rechazada) → no mostrar loader
        if (e.defaultPrevented) return;

        if (form.hasAttribute('hx-post') || form.hasAttribute('hx-get')) return;

        form.classList.add('submitting');
        window._formSubmitting = true;

        // ✅ Deshabilitar el botón que inició el submit (evita doble envío)
        if (e.submitter) {
            e.submitter.classList.add('loading');
            e.submitter.disabled = true;
        }

        showLoader('Procesando...');
    });

    // ============================================
    // 4. Loading para peticiones HTMX
    // ============================================
    document.addEventListener('htmx:beforeRequest', function(e) {
        window._htmxRequest = true;
        const target = e.detail.elt;
        if (!target.hasAttribute('hx-trigger') || !target.getAttribute('hx-trigger').includes('keyup')) {
            progressBar?.classList.add('active');
        }
    });

    document.addEventListener('htmx:afterRequest', function(e) {
        window._htmxRequest = false;
        progressBar?.classList.remove('active');
        progressBar?.classList.add('complete');
        setTimeout(() => progressBar?.classList.remove('complete'), 700);
    });

    document.addEventListener('htmx:responseError', function(e) {
        window._htmxRequest = false;
        hideLoader();
    });

    // ============================================
    // 5. Loading al cargar la página
    // ============================================
    window.addEventListener('load', function() {
        hideLoader();
        window._formSubmitting = false;
    });

    // ============================================
    // 6. Función global para usar desde botones
    // ============================================
    window.showGlobalLoader = showLoader;
    window.hideGlobalLoader = hideLoader;
})();