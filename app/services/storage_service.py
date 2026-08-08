"""
Servicio de almacenamiento de imágenes.
Usa Cloudinary en producción (las imágenes viven en la nube, no en el
filesystem efímero de Render) y almacenamiento local solo en desarrollo.
"""
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app


def upload_image(file):
    """
    Sube una imagen y devuelve su URL pública.
    - Si hay credenciales de Cloudinary → sube a la nube (persistente).
    - Si no → guarda en local (solo desarrollo).
    Devuelve None si falla.
    """
    if current_app.config.get("CLOUDINARY_CLOUD_NAME"):
        return _upload_to_cloudinary(file)
    return _upload_to_local(file)


def _upload_to_cloudinary(file):
    try:
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=current_app.config["CLOUDINARY_CLOUD_NAME"],
            api_key=current_app.config["CLOUDINARY_API_KEY"],
            api_secret=current_app.config["CLOUDINARY_API_SECRET"],
            secure=True,
        )
        result = cloudinary.uploader.upload(
            file,
            folder="marroquineria/productos",
            resource_type="image",
        )
        return result["secure_url"]
    except Exception as e:
        current_app.logger.error(f"❌ Error subiendo a Cloudinary: {e}")
        return None


def _upload_to_local(file):
    """Guarda la imagen en el servidor (solo desarrollo)."""
    try:
        original_filename = secure_filename(file.filename)
        ext = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        save_path = os.path.join(upload_folder, unique_filename)
        file.save(save_path)
        return f"/static/img/products/{unique_filename}"
    except Exception as e:
        current_app.logger.error(f"❌ Error guardando imagen local: {e}")
        return None


def delete_image(image_url):
    """Elimina una imagen de Cloudinary si corresponde (best effort)."""
    if not image_url or "cloudinary.com" not in image_url:
        return
    try:
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=current_app.config["CLOUDINARY_CLOUD_NAME"],
            api_key=current_app.config["CLOUDINARY_API_KEY"],
            api_secret=current_app.config["CLOUDINARY_API_SECRET"],
            secure=True,
        )
        public_id = _extract_public_id(image_url)
        if public_id:
            cloudinary.uploader.destroy(public_id)
    except Exception as e:
        current_app.logger.warning(f"⚠️ No se pudo borrar imagen de Cloudinary: {e}")


def _extract_public_id(image_url):
    """Extrae el public_id desde una URL de Cloudinary."""
    try:
        path = image_url.split("/upload/")[-1]
        parts = path.split("/")
        # eliminar el segmento de versión (v1234567890) si existe
        if parts and parts[0].startswith("v") and parts[0][1:].isdigit():
            parts = parts[1:]
        return "/".join(parts).rsplit(".", 1)[0]
    except Exception:
        return None