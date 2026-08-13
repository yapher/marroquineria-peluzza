# app/services/storage/cloudinary_backend.py
"""
Backend de almacenamiento: Cloudinary.
Se usa en producción (Render) donde el filesystem es efímero.
Las imágenes viven en la nube de forma persistente.
"""
from flask import current_app
from .base import StorageBackend


class CloudinaryBackend(StorageBackend):
    """Sube y elimina imágenes usando la API de Cloudinary."""

    def _configure(self):
        """Configura el SDK de Cloudinary con las credenciales de la app."""
        import cloudinary
        cloudinary.config(
            cloud_name=current_app.config["CLOUDINARY_CLOUD_NAME"],
            api_key=current_app.config["CLOUDINARY_API_KEY"],
            api_secret=current_app.config["CLOUDINARY_API_SECRET"],
            secure=True,
        )

    def upload(self, file) -> str | None:
        """
        Sube una imagen a Cloudinary.
        Devuelve la URL segura (HTTPS) o None si falla.
        """
        try:
            import cloudinary.uploader
            self._configure()

            result = cloudinary.uploader.upload(
                file,
                folder="marroquineria/productos",
                resource_type="image",
            )
            return result["secure_url"]

        except Exception as e:
            current_app.logger.error(f"❌ [Cloudinary] Error subiendo imagen: {e}")
            return None

    def delete(self, image_url: str) -> None:
        """
        Elimina una imagen de Cloudinary.
        Solo actúa si la URL es efectivamente de Cloudinary.
        """
        if not image_url or "cloudinary.com" not in image_url:
            return

        try:
            import cloudinary.uploader
            self._configure()

            public_id = self._extract_public_id(image_url)
            if public_id:
                cloudinary.uploader.destroy(public_id)
                current_app.logger.info(f"🗑️ [Cloudinary] Imagen eliminada: {public_id}")

        except Exception as e:
            current_app.logger.warning(f"⚠️ [Cloudinary] No se pudo borrar imagen: {e}")

    def _extract_public_id(self, image_url: str) -> str | None:
        """
        Extrae el public_id desde una URL de Cloudinary.
        Ejemplo:
            https://res.cloudinary.com/demo/image/upload/v1234/folder/img.jpg
            → 'folder/img'
        """
        try:
            path = image_url.split("/upload/")[-1]
            parts = path.split("/")

            # Eliminar el segmento de versión (v1234567890) si existe
            if parts and parts[0].startswith("v") and parts[0][1:].isdigit():
                parts = parts[1:]

            # Quitar extensión
            return "/".join(parts).rsplit(".", 1)[0]

        except Exception:
            return None