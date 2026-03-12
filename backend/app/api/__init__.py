from flask_restful import Api

from .auth import (
    LoginAPI,
    RegisterAPI,
    RefreshAPI,
    ProfileAPI,
    ProfileImageAPI,
    TechnicianServicesAPI,
    UserProfileAPI,
    TechnicianReviewsAPI,
)
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
    TenantTicketCommentsAPI,
    ManagedTenantsAPI,
    ManagedTicketsAPI,
    ManagedTicketDetailAPI,
    ManagedTicketCommentsAPI,
    ManagedTicketInvalidAPI,
    TicketImageUploadAPI,
    TicketImageDeleteAPI,
    TechnicianTicketsAPI,
    TechnicianTicketDetailAPI,
    TechnicianTicketAcceptAPI,
    TechnicianTicketRejectAPI,
    TechnicianTicketCommentsAPI,
    TechnicianSearchAPI,
    AssignTechnicianAPI,
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
api.add_resource(ProfileImageAPI, "/auth/profile/image")
api.add_resource(UserProfileAPI, "/users/<string:user_id>/profile")
api.add_resource(TechnicianServicesAPI, "/technician/services")
api.add_resource(TechnicianReviewsAPI, "/technicians/<string:technician_id>/reviews")

# Manager–Tenant invitations
api.add_resource(TenantSearchAPI, "/manager/tenants/search")
api.add_resource(SendInvitationAPI, "/manager/invitations")
api.add_resource(SentInvitationsAPI, "/manager/invitations/sent")
api.add_resource(ReceivedInvitationsAPI, "/tenant/invitations")
api.add_resource(RespondInvitationAPI, "/tenant/invitations/<string:invitation_id>")

# Tenant — tickets & notifications
api.add_resource(TenantTicketsAPI, "/tenant/tickets")
api.add_resource(TenantTicketDetailAPI, "/tenant/tickets/<string:ticket_id>")
api.add_resource(TenantTicketCommentsAPI, "/tenant/tickets/<string:ticket_id>/comments")
api.add_resource(TicketImageUploadAPI, "/tenant/tickets/<string:ticket_id>/images")
api.add_resource(TicketImageDeleteAPI, "/tenant/tickets/<string:ticket_id>/images/<string:image_id>")
api.add_resource(TenantNotificationsAPI, "/tenant/notifications")
api.add_resource(MarkNotificationReadAPI, "/tenant/notifications/<string:notification_id>")

# Manager — tenants & tickets
api.add_resource(ManagedTenantsAPI, "/manager/tenants")
api.add_resource(ManagedTicketsAPI, "/manager/tickets")
api.add_resource(ManagedTicketDetailAPI, "/manager/tickets/<string:ticket_id>")
api.add_resource(ManagedTicketCommentsAPI, "/manager/tickets/<string:ticket_id>/comments")
api.add_resource(ManagedTicketInvalidAPI, "/manager/tickets/<string:ticket_id>/invalid")

# Technician — assigned tickets
api.add_resource(TechnicianTicketsAPI, "/technician/tickets")
api.add_resource(TechnicianTicketDetailAPI, "/technician/tickets/<string:ticket_id>")
api.add_resource(TechnicianTicketAcceptAPI, "/technician/tickets/<string:ticket_id>/accept")
api.add_resource(TechnicianTicketRejectAPI, "/technician/tickets/<string:ticket_id>/reject")
api.add_resource(TechnicianTicketCommentsAPI, "/technician/tickets/<string:ticket_id>/comments")

# Manager — technician search & assignment
api.add_resource(TechnicianSearchAPI, "/manager/technicians/search")
api.add_resource(AssignTechnicianAPI, "/manager/tickets/<string:ticket_id>/assign")


def init_app(app):
    api.init_app(app)