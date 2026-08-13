# app/services/storage/__init__.py
"""
Paquete de almacenamiento de imágenes.

API pública:
    from app.services.storage import upload_image, delete_image

El backend se selecciona automáticamente según la configuración:
    - Si hay CLOUDINARY_CLOUD_NAME → CloudinaryBackend
    - Si no → LocalBackend
"""
from flask import current_app
from .cloudinary_backend import CloudinaryBackend
from .local_backend import LocalBackend


def get_backend():
    """
    Factory: devuelve el backend de almacenamiento adecuado
    según la configuración actual de la app.
    """
    if current_app.config.get("CLOUDINARY_CLOUD_NAME"):
        return CloudinaryBackend()
    return LocalBackend()


def upload_image(file):
    """
    Sube una imagen y devuelve su URL pública.
    Devuelve None si falla.
    """
    return get_backend().upload(file)


def delete_image(image_url):
    """
    Elimina una imagen del storage (best effort).
    No lanza excepciones.
    """
    return get_backend().delete(image_url)