# app/blueprints/auth/routes.py
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from . import auth_bp
from ...forms.auth_forms import LoginForm, RegisterForm
from ...models import User
from ...extensions import db
from ...services.auth.oauth_service import (
    is_known_provider,
    is_provider_enabled,
    start_oauth_flow,
    complete_oauth_flow,
)


def _is_safe_url(target):
    if not target:
        return False
    parsed = urlparse(target)
    return parsed.netloc == "" and target.startswith("/")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            # ✅ NUEVO: verificar si el usuario está bloqueado
            if user.is_blocked:
                flash(
                    "🚫 Tu cuenta ha sido bloqueada. Contactá al administrador.",
                    "error"
                )
                return render_template("auth/login.html", form=form)

            login_user(user, remember=form.remember_me.data)
            flash(f"¡Bienvenido/a, {user.first_name}!", "success")
            next_page = request.args.get("next")
            if not _is_safe_url(next_page):
                next_page = None
            return redirect(next_page or url_for("main.index"))

        flash("Email o contraseña incorrectos", "error")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/registro", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        from ...services.email_service import send_welcome_email
        send_welcome_email(user)

        login_user(user)
        flash("¡Cuenta creada exitosamente!", "success")
        return redirect(url_for("main.index"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada", "info")
    return redirect(url_for("main.index"))


# ============================================
# LOGIN SOCIAL (OAuth)
# ============================================
@auth_bp.route("/login/<provider>")
def social_login(provider):
    if not is_known_provider(provider):
        abort(404)

    if not is_provider_enabled(provider):
        flash("El inicio de sesión con ese proveedor no está disponible.", "warning")
        return redirect(url_for("auth.login"))

    result = start_oauth_flow(provider)
    if result is None:
        flash("Error al iniciar el flujo de autenticación. Verificá la configuración.", "error")
        return redirect(url_for("auth.login"))
    return result


@auth_bp.route("/callback/<provider>")
def social_callback(provider):
    if not is_known_provider(provider):
        abort(404)

    user, error = complete_oauth_flow(provider)
    if error:
        flash(error, "error")
        return redirect(url_for("auth.login"))

    # ✅ NUEVO: verificar si el usuario está bloqueado tras login social
    if user.is_blocked:
        flash("🚫 Tu cuenta ha sido bloqueada. Contactá al administrador.", "error")
        return redirect(url_for("auth.login"))

    login_user(user)
    flash(f"¡Bienvenido/a, {user.first_name}!", "success")
    return redirect(url_for("main.index"))