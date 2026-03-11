from flask_restful import Api

from .auth import LoginAPI, RegisterAPI, RefreshAPI, ProfileAPI


api = Api(prefix="/api")

api.add_resource(RegisterAPI, "/auth/register")
api.add_resource(LoginAPI, "/auth/login")
api.add_resource(RefreshAPI, "/auth/refresh")
api.add_resource(ProfileAPI, "/auth/profile")


def init_app(app):
    api.init_app(app)