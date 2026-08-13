# app/services/storage/local_backend.py
"""
Backend de almacenamiento: Filesystem local.
Se usa SOLO en desarrollo. En producción (Render) el filesystem
es efímero y se pierde con cada deploy.
"""
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from .base import StorageBackend


class LocalBackend(StorageBackend):
    """Guarda imágenes en el disco local del servidor."""

    def upload(self, file) -> str | None:
        """
        Guarda la imagen en UPLOAD_FOLDER y devuelve la URL relativa.
        Devuelve None si falla.
        """
        try:
            original_filename = secure_filename(file.filename)
            ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
            unique_filename = f"{uuid.uuid4().hex}.{ext}"

            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)

            save_path = os.path.join(upload_folder, unique_filename)
            file.save(save_path)

            current_app.logger.info(f"💾 [Local] Imagen guardada: {unique_filename}")
            return f"/static/img/products/{unique_filename}"

        except Exception as e:
            current_app.logger.error(f"❌ [Local] Error guardando imagen: {e}")
            return None

    def delete(self, image_url: str) -> None:
        """
        Elimina una imagen del filesystem local.
        Solo actúa si la URL es relativa (no externa).
        """
        if not image_url or image_url.startswith("http"):
            return

        try:
            # Convertir URL relativa a path absoluto
            # "/static/img/products/abc.jpg" → "app/static/img/products/abc.jpg"
            relative_path = image_url.lstrip("/")
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)
            )))  # app/services/storage/ → app/
            file_path = os.path.join(base_dir, relative_path)

            if os.path.exists(file_path):
                os.remove(file_path)
                current_app.logger.info(f"🗑️ [Local] Imagen eliminada: {image_url}")

        except Exception as e:
            current_app.logger.warning(f"⚠️ [Local] No se pudo borrar imagen: {e}")