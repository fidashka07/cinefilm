from datetime import UTC, datetime

from flask import Blueprint, jsonify, render_template
from flask_login import current_user, login_required
from sqlalchemy import select

from src.extensions import db
from src.models import Notification, WatchlistEntry
from src.services.notification_service import NotificationService

notifications = Blueprint(
    "notifications",
    __name__,
    url_prefix="/notifications",
)


@notifications.get("/")
@login_required
def index():
    NotificationService.generate_due(current_user)

    entries = db.session.scalars(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    ).all()

    return render_template(
        "notifications/index.html",
        notifications=entries,
    )


@notifications.get("/unread-count")
@login_required
def unread_count():
    NotificationService.generate_due(current_user)

    return jsonify({
        "count": NotificationService.unread_count(current_user.id)
    })


@notifications.post("/<int:notification_id>/read")
@login_required
def mark_read(notification_id):
    notification = db.session.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )

    if notification is None:
        return jsonify({"error": "Notification not found."}), 404

    notification.read_at = datetime.now(UTC)
    db.session.commit()

    return jsonify({"message": "Notification marked as read."})


@notifications.post("/read-all")
@login_required
def mark_all_read():
    entries = db.session.scalars(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.read_at.is_(None),
        )
    ).all()

    now = datetime.now(UTC)

    for entry in entries:
        entry.read_at = now

    db.session.commit()

    return jsonify({"message": "All notifications marked as read."})


@notifications.get("/watchlist")
@login_required
def watchlist():
    entries = db.session.scalars(
        select(WatchlistEntry)
        .where(WatchlistEntry.user_id == current_user.id)
        .order_by(WatchlistEntry.added_at.desc())
    ).all()

    return render_template(
        "notifications/watchlist.html",
        movies=[entry.movie for entry in entries],
    )
