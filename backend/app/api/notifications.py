from flask_restful import Resource
from flask_jwt_extended import current_user

from app.models import db, Notification, UserRole
from app.utils.RBAC import roles_required


# --------------------------------------------------
# LIST NOTIFICATIONS (Tenant only)
# --------------------------------------------------

class TenantNotificationsAPI(Resource):

    method_decorators = [roles_required(UserRole.TENANT)]

    def get(self):
        notifications = (
            db.session.execute(
                db.select(Notification)
                .filter_by(user_id=current_user.id)
                .order_by(Notification.created_at.desc())
            )
            .scalars()
            .all()
        )

        return {
            "success": True,
            "notifications": [
                {
                    "id": n.id,
                    "message": n.message,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in notifications
            ],
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
