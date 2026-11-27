from datetime import date, timedelta

from sqlalchemy import select

from src.extensions import db
from src.models import Notification, WatchlistEntry


class NotificationService:

    @staticmethod
    def create(user_id, movie, notification_type, message):
        existing = db.session.scalar(
            select(Notification.id).where(
                Notification.user_id == user_id,
                Notification.movie_id == movie.id,
                Notification.notification_type == notification_type,
            )
        )

        if existing:
            return None

        notification = Notification(
            user_id=user_id,
            movie_id=movie.id,
            notification_type=notification_type,
            message=message,
        )

        db.session.add(notification)
        return notification

    @classmethod
    def generate_due(cls, user):
        today = date.today()

        entries = db.session.scalars(
            select(WatchlistEntry).where(
                WatchlistEntry.user_id == user.id
            )
        ).all()

        changed = False

        for entry in entries:
            movie = entry.movie
            release = movie.release_date

            if release is None or release < today:
                continue

            if release == today:
                message = (
                    f"{movie.title} is out today! "
                    "It's time to watch."
                )

                notification_type = "release_day"

            elif release <= today + timedelta(days=7):
                days = (release - today).days

                message = (
                    f"{movie.title} releases in "
                    f"{days} day{'s' if days != 1 else ''}."
                )

                notification_type = "release_reminder"

            else:
                continue

            created = cls.create(
                user.id,
                movie,
                notification_type,
                message,
            )

            if created:
                changed = True

        if changed:
            db.session.commit()

    @staticmethod
    def unread_count(user_id):
        return db.session.scalar(
            select(db.func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
        ) or 0
