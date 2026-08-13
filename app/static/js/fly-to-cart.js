// ============================================
// CARRUSEL DE GALERÍA DE PRODUCTO (Alpine.js)
// Con soporte táctil (swipe) para móvil
// ============================================

function productGallery() {
    return {
        current: 0,
        images: [],
        touchStartX: 0,
        touchEndX: 0,
        isSwiping: false,

        init() {
            const container = this.$el;
            const imageData = container.dataset.images;
            if (imageData) {
                try {
                    this.images = JSON.parse(imageData);
                } catch (e) {
                    console.error('Error parsing gallery images:', e);
                }
            }

            this.$el.addEventListener('touchstart', (e) => {
                this.touchStartX = e.changedTouches[0].screenX;
                this.isSwiping = true;
            }, { passive: true });

            this.$el.addEventListener('touchend', (e) => {
                if (!this.isSwiping) return;
                this.touchEndX = e.changedTouches[0].screenX;
                this.handleSwipe();
                this.isSwiping = false;
            }, { passive: true });
        },

        handleSwipe() {
            const threshold = 50;
            const diff = this.touchStartX - this.touchEndX;
            if (Math.abs(diff) < threshold) return;
            if (diff > 0) {
                this.next();
            } else {
                this.prev();
            }
        },

        next() {
            if (this.images.length <= 1) return;
            this.current = (this.current + 1) % this.images.length;
        },

        prev() {
            if (this.images.length <= 1) return;
            this.current = (this.current - 1 + this.images.length) % this.images.length;
        },

        goTo(index) {
            this.current = index;
        }
    }
}


// ============================================
// FLY TO CART - Animación de producto al carrito
// ============================================

(function() {
    'use strict';

    // ⚡ ACÁ AJUSTÁS LA VELOCIDAD (en segundos)
    const FLY_DURATION = 6;       // ← Duración del vuelo (antes 0.7)
    const PULSE_DURATION = 0.2;     // ← Duración del pulso del carrito (antes 0.3)

    function getProductImage(button) {
        let container = button.closest('.group') ||
                        button.closest('[class*="rounded-xl"]') ||
                        button.closest('[class*="shadow"]') ||
                        button.parentElement.parentElement;

        if (container) {
            const img = container.querySelector('img[src]');
            if (img && img.src && !img.src.includes('data:')) {
                return img;
            }
        }

        const galleryImg = document.querySelector('.gallery-arrow')?.closest('.relative')?.querySelector('img[src]');
        if (galleryImg) return galleryImg;

        const allImgs = document.querySelectorAll('img[src*="/static/img/products"]');
        if (allImgs.length > 0) return allImgs[0];

        return null;
    }

    function getCartTarget() {
        const cartCount = document.getElementById('cart-count');
        const cartLink = document.querySelector('a[href="/checkout/carrito"]');
        if (cartCount) return cartCount.getBoundingClientRect();
        if (cartLink) return cartLink.getBoundingClientRect();
        return null;
    }

    function flyToCart(sourceImg) {
        const cartTarget = getCartTarget();
        if (!cartTarget) return;

        const clone = document.createElement('img');
        clone.src = sourceImg.src;
        clone.alt = sourceImg.alt || 'Producto';

        const sourceRect = sourceImg.getBoundingClientRect();
        const size = 80;

        clone.style.cssText = `
            position: fixed;
            top: ${sourceRect.top + sourceRect.height / 2 - size / 2}px;
            left: ${sourceRect.left + sourceRect.width / 2 - size / 2}px;
            width: ${size}px;
            height: ${size}px;
            border-radius: 50%;
            object-fit: cover;
            z-index: 99999;
            pointer-events: none;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            transition: all ${FLY_DURATION}s cubic-bezier(0.2, 1, 0.3, 1);
            opacity: 1;
            transform: scale(1);
        `;

        document.body.appendChild(clone);

        const targetX = cartTarget.left + cartTarget.width / 2 - size / 2;
        const targetY = cartTarget.top + cartTarget.height / 2 - size / 2;

        clone.offsetHeight; // Forzar reflow

        requestAnimationFrame(() => {
            clone.style.top = `${targetY}px`;
            clone.style.left = `${targetX}px`;
            clone.style.width = '20px';
            clone.style.height = '20px';
            clone.style.opacity = '0.3';
            clone.style.transform = 'scale(0.2)';
            clone.style.borderRadius = '50%';
        });

        // ⚡ Este timeout DEBE coincidir con FLY_DURATION (en ms)
        setTimeout(() => {
            clone.remove();
            pulseCart();
        }, FLY_DURATION * 1000);
    }

    function pulseCart() {
        const cartLink = document.querySelector('a[href="/checkout/carrito"]');
        if (!cartLink) return;

        cartLink.style.transition = `transform ${PULSE_DURATION}s ease`;
        cartLink.style.transform = 'scale(1.3)';

        setTimeout(() => {
            cartLink.style.transform = 'scale(1)';
        }, PULSE_DURATION * 1000);
    }

    document.addEventListener('click', function(e) {
        const button = e.target.closest('[hx-post*="/checkout/agregar/"]') ||
                       e.target.closest('button[type="submit"]');

        if (!button) return;

        const form = button.closest('form');
        const isAddToCart = button.hasAttribute('hx-post') &&
                           button.getAttribute('hx-post').includes('/checkout/agregar/');
        const isFormAddToCart = form && form.getAttribute('hx-post') &&
                               form.getAttribute('hx-post').includes('/checkout/agregar/');

        if (!isAddToCart && !isFormAddToCart) return;

        const img = getProductImage(button);
        if (img) {
            flyToCart(img);
        }
    });

    document.addEventListener('htmx:beforeRequest', function(e) {
        const elt = e.detail.elt;
        const path = elt.getAttribute('hx-post') || '';
        if (!path.includes('/checkout/agregar/')) return;

        const img = getProductImage(elt);
        if (img) {
            flyToCart(img);
        }
    });

})();