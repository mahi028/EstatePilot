from flask_restful import Resource
from flask import request
from flask_jwt_extended import current_user
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from app.models import db, Notification, UserRole
from app.utils.RBAC import roles_required


def _pagination_args(default_size=10, max_size=50):
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1

    try:
        page_size = int(request.args.get("page_size", default_size))
    except (TypeError, ValueError):
        page_size = default_size
    page_size = max(1, min(page_size, max_size))
    return page, page_size


def _serialize_notification(notification):
    return {
        "id": notification.id,
        "message": notification.message,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
    }


def _list_notifications_for_user(user_id):
    q = request.args.get("q", "").strip()
    unread_only = request.args.get("unread", "").strip().lower() in {"1", "true", "yes"}
    page, page_size = _pagination_args(default_size=10)

    query = db.select(Notification).filter(Notification.user_id == user_id)

    if unread_only:
        query = query.filter(Notification.is_read.is_(False))

    if q:
        query = query.filter(Notification.message.ilike(f"%{q}%"))

    query = query.order_by(Notification.created_at.desc())

    total = db.session.execute(
        db.select(func.count()).select_from(query.subquery())
    ).scalar_one()

    notifications = db.session.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    return notifications, {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
    }


# --------------------------------------------------
# LIST NOTIFICATIONS (Tenant only)
# --------------------------------------------------

class TenantNotificationsAPI(Resource):

    method_decorators = [roles_required(UserRole.TENANT)]

    def get(self):
        notifications, pagination = _list_notifications_for_user(current_user.id)

        return {
            "success": True,
            "notifications": [_serialize_notification(n) for n in notifications],
            "pagination": pagination,
        }, 200


# --------------------------------------------------
# MARK NOTIFICATION READ (Tenant only)
# --------------------------------------------------

class MarkNotificationReadAPI(Resource):

    method_decorators = [roles_required(UserRole.TENANT)]

    def patch(self, notification_id):
        notif = db.session.get(Notification, notification_id)

        if not notif or notif.user_id != current_user.id:
            return {"success": False, "message": "Notification not found"}, 404

        notif.mark_read()
        db.session.commit()

        return {"success": True, "message": "Notification marked as read"}, 200


class UserNotificationsAPI(Resource):

    method_decorators = [jwt_required()]

    def get(self):
        notifications, pagination = _list_notifications_for_user(current_user.id)

        return {
            "success": True,
            "notifications": [_serialize_notification(n) for n in notifications],
            "pagination": pagination,
        }, 200


class MarkUserNotificationReadAPI(Resource):

    method_decorators = [jwt_required()]

    def patch(self, notification_id):
        notif = db.session.get(Notification, notification_id)

        if not notif or notif.user_id != current_user.id:
            return {"success": False, "message": "Notification not found"}, 404

        notif.mark_read()
        db.session.commit()

        return {"success": True, "message": "Notification marked as read"}, 200
