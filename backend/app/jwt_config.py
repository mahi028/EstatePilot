from datetime import timedelta

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    verify_jwt_in_request,
    current_user,
    JWTManager
)

from flask import jsonify

from app.models import db, User, UserRole


jwt_manager = JWTManager()


# ---------------------------------------------------
# USER IDENTITY HANDLING
# ---------------------------------------------------

@jwt_manager.user_identity_loader
def user_identity_lookup(user):
    """
    Defines what gets stored in JWT 'sub'
    """
    return user.id


@jwt_manager.user_lookup_loader # type: ignore
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return db.session.get(User, identity)


# ---------------------------------------------------
# TOKEN CREATION
# ---------------------------------------------------

def generate_tokens(user):
    """
    Create access + refresh tokens
    """

    additional_claims = {
        "role": user.role.value
    }

    access_token = create_access_token(
        identity=user,
        additional_claims=additional_claims, # type: ignore
        expires_delta=timedelta(hours=8)
    )

    refresh_token = create_refresh_token(
        identity=user,
        expires_delta=timedelta(days=7)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }


# ---------------------------------------------------
# CURRENT USER HELPERS
# ---------------------------------------------------

def get_current_user():
    """
    Ensures JWT is valid and returns user
    """

    verify_jwt_in_request()

    return current_user


def get_current_user_id():
    verify_jwt_in_request()
    return get_jwt_identity()


# ---------------------------------------------------
# ROLE PROTECTION DECORATORS
# ---------------------------------------------------

def require_role(role: UserRole):
    """
    Protect route by role
    """

    def wrapper(fn):

        def decorator(*args, **kwargs):

            verify_jwt_in_request()

            if not current_user:
                return jsonify({"error": "User not found"}), 401

            if current_user.role != role:
                return jsonify({"error": "Unauthorized"}), 403

            return fn(*args, **kwargs)

        decorator.__name__ = fn.__name__
        return decorator

    return wrapper


def require_roles(*roles):
    """
    Allow multiple roles
    """

    def wrapper(fn):

        def decorator(*args, **kwargs):

            verify_jwt_in_request()

            if not current_user:
                return jsonify({"error": "User not found"}), 401

            if current_user.role not in roles:
                return jsonify({"error": "Unauthorized"}), 403

            return fn(*args, **kwargs)

        decorator.__name__ = fn.__name__
        return decorator

    return wrapper


# ---------------------------------------------------
# ERROR HANDLERS
# ---------------------------------------------------

@jwt_manager.unauthorized_loader
def unauthorized_callback(error):
    return jsonify({
        "error": "Authorization header missing"
    }), 401


@jwt_manager.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        "error": "Invalid token"
    }), 401


@jwt_manager.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        "error": "Token expired"
    }), 401


@jwt_manager.user_lookup_error_loader # type: ignore
def user_lookup_error(jwt_header, jwt_data):
    return jsonify({
        "error": "User not found"
    }), 401