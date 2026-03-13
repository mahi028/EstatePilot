from flask_restful import Resource
from flask import request
from flask_jwt_extended import current_user

from app.models import db, User, UserRole, TenantProfile, ManagementInvitation, InvitationStatus, Notification
from app.forms import SendInvitationForm
from app.utils.RBAC import roles_required


def _serialize_invitation(inv):
    return {
        "id": inv.id,
        "manager": {
            "id": inv.manager_user.id,
            "name": inv.manager_user.name,
            "email": inv.manager_user.email,
        },
        "tenant": {
            "id": inv.tenant_user.id,
            "name": inv.tenant_user.name,
            "email": inv.tenant_user.email,
        },
        "status": inv.status.value,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
    }


# --------------------------------------------------
# SEARCH TENANTS (Manager only)
# --------------------------------------------------

class TenantSearchAPI(Resource):

    method_decorators = [roles_required(UserRole.MANAGER)]

    def get(self):
        q = request.args.get("q", "").strip()
        if len(q) < 2:
            return {"success": False, "message": "Search query must be at least 2 characters"}, 400

        tenants = db.session.execute(
            db.select(User)
            .filter(User.role == UserRole.TENANT)
            .outerjoin(TenantProfile, TenantProfile.user_id == User.id)
            .filter(TenantProfile.manager_id.is_(None))
            .filter(
                db.or_(
                    User.name.ilike(f"%{q}%"),
                    User.email.ilike(f"%{q}%"),
                )
            )
            .limit(20)
        ).scalars().all()

        return {
            "success": True,
            "tenants": [
                {
                    "id": t.id,
                    "name": t.name,
                    "email": t.email,
                }
                for t in tenants
            ],
        }, 200


# --------------------------------------------------
# SEND INVITATION (Manager only)
# --------------------------------------------------

class SendInvitationAPI(Resource):

    method_decorators = [roles_required(UserRole.MANAGER)]

    def post(self):
        form = SendInvitationForm(data=request.json)

        if not form.validate():
            return {"success": False, "errors": form.errors}, 400

        # Check for existing pending request
        existing = db.session.execute(
            db.select(ManagementInvitation).filter_by(
                manager_id=current_user.id,
                tenant_id=form.tenant_id.data,
                status=InvitationStatus.PENDING,
            )
        ).scalar_one_or_none()

        if existing:
            return {"success": False, "message": "A pending invitation already exists for this tenant"}, 409

        req = ManagementInvitation(
            manager_id=current_user.id,
            tenant_id=form.tenant_id.data,
        )
        db.session.add(req)
        db.session.commit()

        return {"success": True, "message": "Invitation sent", "invitation": _serialize_invitation(req)}, 201


# --------------------------------------------------
# LIST SENT INVITATIONS (Manager only)
# --------------------------------------------------

class SentInvitationsAPI(Resource):

    method_decorators = [roles_required(UserRole.MANAGER)]

    def get(self):
        status_filter = request.args.get("status")
        query = db.select(ManagementInvitation).filter_by(manager_id=current_user.id)

        if status_filter:
            try:
                query = query.filter_by(status=InvitationStatus(status_filter))
            except ValueError:
                return {"success": False, "message": "Invalid status filter"}, 400

        query = query.order_by(ManagementInvitation.created_at.desc())
        invitations = db.session.execute(query).scalars().all()

        return {
            "success": True,
            "invitations": [_serialize_invitation(r) for r in invitations],
        }, 200


# --------------------------------------------------
# RECEIVED INVITATIONS (Tenant only)
# --------------------------------------------------

class ReceivedInvitationsAPI(Resource):

    method_decorators = [roles_required(UserRole.TENANT)]

    def get(self):
        status_filter = request.args.get("status")
        query = db.select(ManagementInvitation).filter_by(tenant_id=current_user.id)

        if status_filter:
            try:
                query = query.filter_by(status=InvitationStatus(status_filter))
            except ValueError:
                return {"success": False, "message": "Invalid status filter"}, 400

        query = query.order_by(ManagementInvitation.created_at.desc())
        invitations = db.session.execute(query).scalars().all()

        return {
            "success": True,
            "invitations": [_serialize_invitation(r) for r in invitations],
        }, 200


# --------------------------------------------------
# RESPOND TO INVITATION (Tenant only — accept/reject)
# --------------------------------------------------

class RespondInvitationAPI(Resource):

    method_decorators = [roles_required(UserRole.TENANT)]

    def patch(self, invitation_id):
        invitation = db.session.get(ManagementInvitation, invitation_id)
        if not invitation or invitation.tenant_id != current_user.id:
            return {"success": False, "message": "Invitation not found"}, 404

        action = (request.json or {}).get("action")
        if action not in ("accept", "reject"):
            return {"success": False, "message": "Action must be 'accept' or 'reject'"}, 400

        try:
            if action == "accept":
                invitation.accept()
            else:
                invitation.reject()
        except ValueError as e:
            return {"success": False, "message": str(e)}, 400

        db.session.commit()

        return {
            "success": True,
            "message": f"Invitation {action}ed",
            "invitation": _serialize_invitation(invitation),
        }, 200


# --------------------------------------------------
# TENANT REMOVES CURRENT MANAGER (Tenant only)
# --------------------------------------------------

class RemoveTenantManagerAPI(Resource):

    method_decorators = [roles_required(UserRole.TENANT)]

    def delete(self):
        manager = current_user.manager
        if not manager:
            return {"success": False, "message": "No manager assigned"}, 400

        current_user.manager_id = None

        Notification.create(
            user_id=manager.id,
            message=f"Tenant {current_user.name} removed you as manager",
        )

        db.session.commit()
        return {
            "success": True,
            "message": "Manager removed",
        }, 200


# --------------------------------------------------
# MANAGER REMOVES A MANAGED TENANT (Manager only)
# --------------------------------------------------

class RemoveManagedTenantAPI(Resource):

    method_decorators = [roles_required(UserRole.MANAGER)]

    def delete(self, tenant_id):
        tenant = db.session.get(User, tenant_id)
        if not tenant or tenant.role != UserRole.TENANT:
            return {"success": False, "message": "Tenant not found"}, 404

        if tenant.manager_id != current_user.id:
            return {"success": False, "message": "Tenant not found in your managed list"}, 404

        tenant.manager_id = None

        Notification.create(
            user_id=tenant.id,
            message=f"Manager {current_user.name} removed you from managed tenants",
        )

        db.session.commit()

        return {
            "success": True,
            "message": "Tenant removed",
            "tenant": {
                "id": tenant.id,
                "name": tenant.name,
                "email": tenant.email,
            },
        }, 200
