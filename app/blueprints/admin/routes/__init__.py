"""
Módulo de rutas del panel de administración.
Cada funcionalidad está separada en su propio archivo para mejor mantenibilidad.
"""
from flask import request
from flask_login import login_required, current_user
from functools import wraps
import os

from .. import admin_bp
from ....extensions import db
from ....models import Product, ProductImage, Order, OrderItem, User, Category, Coupon, Review
from ....forms.admin_forms import ProductForm, CategoryForm
from ....forms.coupon_forms import CouponForm
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from ....services.loyalty_service import award_points_for_order


# ============================================
# DECORADORES Y FUNCIONES AUXILIARES
# ============================================

def admin_required(f):
    """Decorador que verifica si el usuario es administrador."""
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            from flask import flash, redirect, url_for
            flash("Acceso restringido. Solo administradores.", "error")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return wrapper


def _get_bool(field_name):
    """Lee booleanos del POST. Un checkbox desmarcado NO se envía."""
    return field_name in request.form


def _process_extra_images(files, product, start_position=0):
    """Sube imágenes adicionales de galería validando cantidad, tamaño y extensión."""
    from flask import current_app, flash
    from ....services.storage_service import upload_image
    
    max_images = current_app.config.get("MAX_EXTRA_IMAGES", 8)
    max_size_mb = current_app.config.get("MAX_IMAGE_SIZE_MB", 5)
    allowed_ext = current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "webp"})
    
    valid_files = [f for f in files if f and f.filename]
    if not valid_files:
        return 0
    
    existing_count = len(product.images)
    available_slots = max_images - existing_count
    
    if available_slots <= 0:
        flash(f"⚠️ Ya tenés {existing_count} imágenes en galería (máximo: {max_images}).", "warning")
        return 0
    
    if len(valid_files) > available_slots:
        flash(f"⚠️ Seleccionaste {len(valid_files)} imágenes, solo quedan {available_slots} lugares. Se subirán las primeras {available_slots}.", "warning")
        valid_files = valid_files[:available_slots]
    
    uploaded_count = 0
    position = start_position
    
    for extra_file in valid_files:
        ext = extra_file.filename.rsplit(".", 1)[-1].lower() if "." in extra_file.filename else ""
        if ext not in allowed_ext:
            flash(f"⚠️ '{extra_file.filename}' no es formato válido. No se subió.", "warning")
            continue
        
        extra_file.seek(0, os.SEEK_END)
        size_mb = extra_file.tell() / (1024 * 1024)
        extra_file.seek(0)
        
        if size_mb > max_size_mb:
            flash(f"⚠️ '{extra_file.filename}' pesa {size_mb:.1f}MB, supera {max_size_mb}MB. No se subió.", "warning")
            continue
        
        try:
            url = upload_image(extra_file)
            if url:
                db.session.add(ProductImage(
                    url=url, alt=product.name, position=position,
                    is_primary=False, product_id=product.id,
                ))
                position += 1
                uploaded_count += 1
            else:
                flash(f"⚠️ No se pudo subir '{extra_file.filename}'.", "warning")
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error subiendo '{extra_file.filename}': {e}")
            flash(f"⚠️ Error subiendo '{extra_file.filename}'.", "warning")
    
    return uploaded_count


# ============================================
# IMPORTAR TODAS LAS RUTAS
# ============================================
from . import dashboard
from . import products
from . import categories
from . import orders
from . import coupons
from . import stats
from . import reviews