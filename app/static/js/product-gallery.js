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
            // Las imágenes se inyectan desde el template via data-images
            const container = this.$el;
            const imageData = container.dataset.images;
            if (imageData) {
                try {
                    this.images = JSON.parse(imageData);
                } catch (e) {
                    console.error('Error parsing gallery images:', e);
                }
            }

            // Agregar listeners de touch para swipe
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
                // Swipe izquierda → siguiente imagen
                this.next();
            } else {
                // Swipe derecha → imagen anterior
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