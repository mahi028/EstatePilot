from functools import wraps
from flask import request, abort
from flask_jwt_extended import jwt_required, current_user
from app import csrf, UserRole

def roles_required(*roles: UserRole):
    """RBAC decorator"""

    def decorator(fn):
        @wraps(fn)
        @jwt_required
        def wrapper(*args, **kwargs):

            if current_user.flag:
                abort(403, description="Account disabled")

            if current_user.role not in roles:
                abort(403, description="Unauthorized")

            return fn(*args, **kwargs)

        return wrapper
    return decorator


def csrf_protected(fn):
    """Enables Flask WTF CSRF Protection for FlaskForms"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.method != 'GET':
            csrf_token = request.headers.get('X-CSRf-Token')
            if not csrf_token:
                csrf_token = request.form.get('csrf_token')
            print(csrf_token)
            if not csrf_token:
                print('CSRF token missing')
                abort(400, description="CSRF token missing")
            try:
                csrf.protect()
            except Exception as err:
                print(err)
                abort(400, description="CSRF token invalid")
        return fn(*args, **kwargs)
    return wrapper