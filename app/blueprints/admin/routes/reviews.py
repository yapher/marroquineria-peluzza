"""Rutas para moderación de reseñas."""
from flask import render_template, request, flash, redirect, url_for, current_app
from .. import admin_bp
from ....models import Review
from ....extensions import db
from ....services.email_service import send_review_approved
from . import admin_required


@admin_bp.route("/reseñas")
@admin_required
def reviews():
    """Lista reseñas con filtros."""
    status_filter = request.args.get("status", "pending")
    query = Review.query.join(Review.user).join(Review.product)
    
    if status_filter == "pending":
        query = query.filter(Review.approved == False)
    elif status_filter == "approved":
        query = query.filter(Review.approved == True)
    
    reviews_list = query.order_by(Review.created_at.desc()).all()
    stats = {
        "total": Review.query.count(),
        "pending": Review.query.filter_by(approved=False).count(),
        "approved": Review.query.filter_by(approved=True).count(),
    }
    return render_template("admin/reviews.html", reviews=reviews_list, stats=stats, current_status=status_filter)


@admin_bp.route("/reseñas/<int:review_id>/aprobar", methods=["POST"])
@admin_required
def approve_review(review_id):
    """Aprueba una reseña y notifica al usuario."""
    review = Review.query.get_or_404(review_id)
    review.approved = True
    db.session.commit()
    
    try:
        send_review_approved(review)
    except Exception as e:
        current_app.logger.error(f"Error enviando email: {e}")
    
    flash(f"✅ Reseña de {review.user.first_name} aprobada", "success")
    return redirect(url_for("admin.reviews", status=request.args.get("status", "pending")))


@admin_bp.route("/reseñas/<int:review_id>/rechazar", methods=["POST"])
@admin_required
def reject_review(review_id):
    """Rechaza y elimina una reseña."""
    review = Review.query.get_or_404(review_id)
    user_name = review.user.first_name
    product_name = review.product.name
    db.session.delete(review)
    db.session.commit()
    flash(f"❌ Reseña de {user_name} para {product_name} rechazada", "warning")
    return redirect(url_for("admin.reviews", status=request.args.get("status", "pending")))