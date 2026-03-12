from flask_restful import Api

from .auth import LoginAPI, RegisterAPI, RefreshAPI, ProfileAPI
from .invitations import (
    TenantSearchAPI,
    SendInvitationAPI,
    SentInvitationsAPI,
    ReceivedInvitationsAPI,
    RespondInvitationAPI,
)
from .tickets import (
    TenantTicketsAPI,
    TenantTicketDetailAPI,
    ManagedTenantsAPI,
    ManagedTicketsAPI,
)
from .notifications import (
    TenantNotificationsAPI,
    MarkNotificationReadAPI,
)


api = Api(prefix="/api")

# Auth
api.add_resource(RegisterAPI, "/auth/register")
api.add_resource(LoginAPI, "/auth/login")
api.add_resource(RefreshAPI, "/auth/refresh")
api.add_resource(ProfileAPI, "/auth/profile")

# Manager–Tenant invitations
api.add_resource(TenantSearchAPI, "/manager/tenants/search")
api.add_resource(SendInvitationAPI, "/manager/invitations")
api.add_resource(SentInvitationsAPI, "/manager/invitations/sent")
api.add_resource(ReceivedInvitationsAPI, "/tenant/invitations")
api.add_resource(RespondInvitationAPI, "/tenant/invitations/<string:invitation_id>")

# Tenant — tickets & notifications
api.add_resource(TenantTicketsAPI, "/tenant/tickets")
api.add_resource(TenantTicketDetailAPI, "/tenant/tickets/<string:ticket_id>")
api.add_resource(TenantNotificationsAPI, "/tenant/notifications")
api.add_resource(MarkNotificationReadAPI, "/tenant/notifications/<string:notification_id>")

# Manager — tenants & tickets
api.add_resource(ManagedTenantsAPI, "/manager/tenants")
api.add_resource(ManagedTicketsAPI, "/manager/tickets")


def init_app(app):
    api.init_app(app)