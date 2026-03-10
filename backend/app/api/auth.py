from flask_restful import Resource
from flask import request

from app.models import db, User, UserRole
from app.forms import RegisterForm, LoginForm
from app.jwt_config import generate_tokens


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
            role=UserRole(form.role.data)
        )

        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        tokens = generate_tokens(user)

        return {
            "success": True,
            "message": "User registered successfully",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value
            },
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

        user = User.query.filter_by(
            email=form.email.data
        ).first()

        if not user or not user.check_password(form.password.data):
            return {
                "success": False,
                "message": "Invalid email or password"
            }, 401

        tokens = generate_tokens(user)

        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value
            },
            **tokens
        }, 200