from urllib.parse import urljoin, urlsplit

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_user, logout_user

from src.extensions import db
from src.forms import LoginForm, RegistrationForm
from src.models import User

auth = Blueprint("auth", __name__, url_prefix="/auth")


def is_safe_redirect_url(target):
    if not target:
        return False

    ref_url = urlsplit(request.host_url)
    test_url = urlsplit(urljoin(request.host_url, target))

    return (
        test_url.scheme in {"http", "https"}
        and ref_url.netloc == test_url.netloc
    )


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
        )

        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Your account has been created. You can now log in.", "success")

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)

            next_page = request.args.get("next")

            if is_safe_redirect_url(next_page):
                return redirect(next_page)

            flash("Welcome back!", "success")
            return redirect(url_for("index"))

        flash("Invalid email or password.", "error")

    return render_template("auth/login.html", form=form)


@auth.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("You have been logged out.", "success")

    return redirect(url_for("index"))