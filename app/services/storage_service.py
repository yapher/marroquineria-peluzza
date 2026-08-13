# app/services/storage_service.py
"""
Fachada pública del servicio de almacenamiento.

Mantiene la misma API que antes para no romper ningún import existente:
    from app.services.storage_service import upload_image, delete_image

Internamente delega al paquete `storage/` que selecciona
el backend adecuado (Cloudinary o Local) según la configuración.
"""
from .storage import upload_image, delete_image  # noqa: F401

# Re-exportar para compatibilidad con imports existentes.
# Cualquier archivo que haga:
#   from ....services.storage_service import upload_image, delete_image
# seguirá funcionando sin cambios.