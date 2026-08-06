from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from . import auth_bp
from ...forms.auth_forms import LoginForm, RegisterForm
from ...models import User
from ...extensions import db


def _is_safe_url(target):
    """✅ Evita open redirect: solo permite URLs internas."""
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