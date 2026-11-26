from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from wtforms.validators import ValidationError
from flask import abort
from src.extensions import db
from src.forms import ProfileForm
from src.models import User

profiles = Blueprint("profiles", __name__)


@profiles.route("/u/<string:username>")
def view_profile(username):
    user = User.query.filter_by(username=username).first_or_404()

    return render_template(
        "profiles/profile.html",
        profile=user,
        is_owner=current_user.is_authenticated
        and current_user.id == user.id,
    )


@profiles.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = ProfileForm()

    if form.validate_on_submit():
        for field in ("avatar_url", "website_url", "instagram_url"):
            value = getattr(form, field).data.strip()

            if value and not value.startswith(("https://", "http://")):
                form.errors.setdefault(field, []).append(
                    "Please enter a valid URL starting with http:// or https://."
                )

        if form.errors:
            return render_template("profiles/edit.html", form=form)

        current_user.display_name = form.display_name.data.strip() or None
        current_user.bio = form.bio.data.strip() or None
        current_user.avatar_url = form.avatar_url.data.strip() or None
        current_user.website_url = form.website_url.data.strip() or None
        current_user.instagram_url = form.instagram_url.data.strip() or None

        current_user.favorite_genres = [
            item.strip()
            for item in form.favorite_genres.data.splitlines()
            if item.strip()
        ][:10]

        current_user.top_movies = [
            item.strip()
            for item in form.top_movies.data.splitlines()
            if item.strip()
        ][:5]

        current_user.top_actors = [
            item.strip()
            for item in form.top_actors.data.splitlines()
            if item.strip()
        ][:5]

        db.session.commit()

        flash("Your profile has been updated.", "success")

        return redirect(
            url_for("profiles.view_profile", username=current_user.username)
        )

    if not form.is_submitted():
        form.display_name.data = current_user.display_name or ""
        form.bio.data = current_user.bio or ""
        form.avatar_url.data = current_user.avatar_url or ""
        form.website_url.data = current_user.website_url or ""
        form.instagram_url.data = current_user.instagram_url or ""

        form.favorite_genres.data = "\n".join(
            current_user.favorite_genres or []
        )

        form.top_movies.data = "\n".join(
            current_user.top_movies or []
        )

        form.top_actors.data = "\n".join(
            current_user.top_actors or []
        )

    return render_template("profiles/edit.html", form=form)

@profiles.post("/u/<string:username>/follow")
@login_required
def follow_user(username):
    user = User.query.filter_by(username=username).first_or_404()

    if current_user.id == user.id:
        flash("You cannot follow yourself.", "error")
        return redirect(url_for("profiles.view_profile", username=username))

    if not current_user.is_following(user):
        current_user.following.append(user)
        db.session.commit()
        flash(f"You are now following {user.username}.", "success")

    return redirect(url_for("profiles.view_profile", username=username))


@profiles.post("/u/<string:username>/unfollow")
@login_required
def unfollow_user(username):
    user = User.query.filter_by(username=username).first_or_404()

    if current_user.is_following(user):
        current_user.following.remove(user)
        db.session.commit()
        flash(f"You unfollowed {user.username}.", "success")

    return redirect(url_for("profiles.view_profile", username=username))


@profiles.get("/u/<string:username>/followers")
def view_followers(username):
    user = User.query.filter_by(username=username).first_or_404()

    return render_template(
        "profiles/followers.html",
        profile=user,
        users=user.followers,
        heading="Followers",
    )


@profiles.get("/u/<string:username>/following")
def view_following(username):
    user = User.query.filter_by(username=username).first_or_404()

    return render_template(
        "profiles/followers.html",
        profile=user,
        users=user.following,
        heading="Following",
    )