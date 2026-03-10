from flask_restful import Api

from .auth import LoginAPI, RegisterAPI


api = Api(prefix="/api")


def init_app(app):

    api.init_app(app)
    api.add_resource(RegisterAPI, "/auth/register")
    api.add_resource(LoginAPI, "/auth/login")