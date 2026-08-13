# app/services/product_image_service.py
"""
Servicio de gestión de imágenes de productos.

Centraliza la validación, subida y persistencia de imágenes de galería
para que las rutas del admin queden declarativas y la lógica sea testeable.
"""
import os
from flask import current_app, flash
from ..extensions import db
from ..models import ProductImage
from .storage_service import upload_image


def validate_image_file(file, max_size_mb: int, allowed_extensions: set) -> tuple[bool, str]:
    """
    Valida un archivo de imagen individual.
    Devuelve (es_valido, mensaje_error).
    """
    if not file or not file.filename:
        return False, "Archivo vacío"

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed_extensions:
        return False, f"'{file.filename}' no es formato válido ({ext}). Formatos permitidos: {', '.join(allowed_extensions)}"

    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)

    if size_mb > max_size_mb:
        return False, f"'{file.filename}' pesa {size_mb:.1f}MB, supera el límite de {max_size_mb}MB"

    return True, ""


def get_available_slots(product) -> int:
    """Calcula cuántas imágenes más se pueden agregar a un producto."""
    max_images = current_app.config.get("MAX_EXTRA_IMAGES", 8)
    existing_count = len(product.images)
    return max(0, max_images - existing_count)


def process_extra_images(files, product, start_position: int = 0) -> int:
    """
    Sube imágenes adicionales de galería validando cantidad, tamaño y extensión.

    Args:
        files: Lista de FileStorage del request (request.files.getlist('extra_images'))
        product: Objeto Product al que se le agregan las imágenes
        start_position: Posición inicial para ordenar en la galería

    Returns:
        int: Cantidad de imágenes subidas exitosamente
    """
    max_size_mb = current_app.config.get("MAX_IMAGE_SIZE_MB", 5)
    allowed_ext = current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "webp"})

    valid_files = [f for f in files if f and f.filename]
    if not valid_files:
        return 0

    # Verificar slots disponibles
    available_slots = get_available_slots(product)
    existing_count = len(product.images)
    max_images = current_app.config.get("MAX_EXTRA_IMAGES", 8)

    if available_slots <= 0:
        flash(f"⚠️ Ya tenés {existing_count} imágenes en galería (máximo: {max_images}).", "warning")
        return 0

    # Si hay más archivos que slots, avisar y truncar
    if len(valid_files) > available_slots:
        flash(
            f"⚠️ Seleccionaste {len(valid_files)} imágenes, solo quedan {available_slots} lugares. "
            f"Se subirán las primeras {available_slots}.",
            "warning"
        )
        valid_files = valid_files[:available_slots]

    uploaded_count = 0
    position = start_position

    for extra_file in valid_files:
        # Validar archivo
        is_valid, error_msg = validate_image_file(extra_file, max_size_mb, allowed_ext)
        if not is_valid:
            flash(f"⚠️ {error_msg}. No se subió.", "warning")
            continue

        # Subir al storage
        try:
            url = upload_image(extra_file)
            if url:
                db.session.add(ProductImage(
                    url=url,
                    alt=product.name,
                    position=position,
                    is_primary=False,
                    product_id=product.id,
                ))
                position += 1
                uploaded_count += 1
            else:
                flash(f"⚠️ No se pudo subir '{extra_file.filename}'.", "warning")
        except Exception as e:
            current_app.logger.error(f"Error subiendo '{extra_file.filename}': {e}")
            flash(f"⚠️ Error subiendo '{extra_file.filename}'.", "warning")

    return uploaded_count


def set_primary_image(product, image):
    """
    Intercambia la imagen principal con una de la galería.
    Si el producto no tiene imagen principal, la promueve directamente.

    Args:
        product: Objeto Product
        image: Objeto ProductImage de la galería
    """
    if not product.image_url:
        # No hay imagen principal → promover directamente
        product.image_url = image.url
        db.session.delete(image)
        db.session.commit()
        flash("✅ Imagen establecida como principal", "success")
        return

    # Intercambiar URLs
    old_primary_url = product.image_url
    product.image_url = image.url
    image.url = old_primary_url
    db.session.commit()
    flash("✅ Imagen establecida como principal. La anterior pasó a la galería.", "success")