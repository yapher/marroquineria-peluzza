// ============================================
// CARRUSEL DE GALERÍA DE PRODUCTO (Alpine.js)
// ============================================
function productGallery() {
    return {
        current: 0,
        images: [],
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
        },
        next() {
            this.current = (this.current + 1) % this.images.length;
        },
        prev() {
            this.current = (this.current - 1 + this.images.length) % this.images.length;
        }
    }
}