from functools import wraps
from flask import request, abort
from flask_jwt_extended import jwt_required, current_user
from app.models import UserRole


def roles_required(*roles: UserRole):
    """RBAC decorator — requires JWT and checks user role."""

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            if current_user.role not in roles:
                abort(403, description="Unauthorized")

            return fn(*args, **kwargs)

        return wrapper
    return decorator