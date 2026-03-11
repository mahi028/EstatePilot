from flask_restful import Resource
from flask import request
from flask_jwt_extended import jwt_required, current_user, get_jwt

from app.models import db, User, UserRole
from app.forms import RegisterForm, LoginForm
from app.jwt_config import generate_tokens


def _serialize_user(user):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
        "manager_id": user.manager_id,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

class RegisterAPI(Resource):

    def post(self):

        form = RegisterForm(data=request.json)

        if not form.validate():
            return {
                "success": False,
                "errors": form.errors
            }, 400

        user = User(
            name=form.name.data,
            email=form.email.data,
            role=UserRole(form.role.data),
            manager_id=form.manager_id.data or None,
        )

        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        tokens = generate_tokens(user)

        return {
            "success": True,
            "message": "User registered successfully",
            "user": _serialize_user(user),
            **tokens
        }, 201


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

class LoginAPI(Resource):

    def post(self):

        form = LoginForm(data=request.json)

        if not form.validate():
            return {
                "success": False,
                "errors": form.errors
            }, 400

        user = db.session.execute(
            db.select(User).filter_by(email=form.email.data)
        ).scalar_one_or_none()

        if not user or not user.check_password(form.password.data):
            return {
                "success": False,
                "message": "Invalid email or password"
            }, 401

        tokens = generate_tokens(user)

        return {
            "success": True,
            "message": "Login successful",
            "user": _serialize_user(user),
            **tokens
        }, 200


# --------------------------------------------------
# TOKEN REFRESH
# --------------------------------------------------

class RefreshAPI(Resource):

    @jwt_required(refresh=True)
    def post(self):
        tokens = generate_tokens(current_user)
        return {
            "success": True,
            **tokens
        }, 200


# --------------------------------------------------
# CURRENT USER PROFILE
# --------------------------------------------------

class ProfileAPI(Resource):

    @jwt_required()
    def get(self):
        return {
            "success": True,
            "user": _serialize_user(current_user),
        }, 200